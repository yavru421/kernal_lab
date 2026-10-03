// kernel_host.exe — kernel_lab registered runner (Option B), version 0.3.2.
// Native only, zero subprocesses inside runner:
//   ledger  : DuckDB C API in-process (libduckdb v1.5.6), prepared statements
//   GPU     : NVML in-process (nvml.dll from driver; header/lib from CUDA 12.6)
//   hashing : BCrypt SHA-256 in-process
//   timing  : QueryPerformanceCounter (wall) + cudaEvent (gpu)
//   video in: Hardware NVDEC stream via ffmpeg pipe
//   video out: Hardware NVENC stream via ffmpeg pipe (outputs/tracked.mp4)
// Supported execution shapes:
//   - init_only: executes symbol_init
//   - init_step_release (cu_geopin_solver): cu_geopin_init -> cu_geopin_extract_patches -> continuous cu_geopin_track_step -> outputs/track.json + outputs/tracked.mp4

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <cuda_runtime.h>
#include <nvml.h>
#include "duckdb.h"
#include <algorithm>
#include <climits>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;
static const char* HOST_VERSION = "kernel_host/0.3.2";

// ---------------------------------------------------------------- utils
static std::string json_s(const std::string& s) {
    std::string o = "\"";
    for (char c : s) {
        switch (c) {
            case '"': o += "\\\""; break; case '\\': o += "\\\\"; break;
            case '\n': o += "\\n"; break; case '\r': o += "\\r"; break; case '\t': o += "\\t"; break;
            default: o += c;
        }
    }
    return o + "\"";
}
static bool read_file(const std::string& p, std::string& out) {
    std::ifstream f(p, std::ios::binary); if (!f) return false;
    std::stringstream ss; ss << f.rdbuf(); out = ss.str(); return true;
}
static bool write_file(const std::string& p, const std::string& s) {
    std::ofstream f(p, std::ios::binary); if (!f) return false; f << s; return (bool)f;
}
static std::string now_local(const char* fmt) {
    std::time_t t = std::time(nullptr); std::tm tm{}; localtime_s(&tm, &t);
    char b[64]; std::strftime(b, sizeof b, fmt, &tm); return b;
}
static std::string win_err(DWORD code) {
    char* msg = nullptr;
    FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
                   nullptr, code, 0, (LPSTR)&msg, 0, nullptr);
    std::string s = "GetLastError=" + std::to_string(code) + " " + (msg ? msg : "");
    if (msg) LocalFree(msg);
    while (!s.empty() && (s.back() == '\n' || s.back() == '\r')) s.pop_back();
    return s;
}
static double qpc_ms() {
    static LARGE_INTEGER f = [] { LARGE_INTEGER x; QueryPerformanceFrequency(&x); return x; }();
    LARGE_INTEGER c; QueryPerformanceCounter(&c); return 1000.0 * (double)c.QuadPart / (double)f.QuadPart;
}
static std::string cuda_err(const char* what, cudaError_t e) {
    return std::string(what) + ": " + cudaGetErrorName(e) + ": " + cudaGetErrorString(e);
}
static std::string jget(const std::string& j, const std::string& key) {
    auto k = j.find("\"" + key + "\""); if (k == std::string::npos) return "";
    auto c = j.find(':', k); if (c == std::string::npos) return "";
    auto p = j.find_first_not_of(" \t\r\n", c + 1); if (p == std::string::npos) return "";
    if (j[p] == '"') { auto e = j.find('"', p + 1); return j.substr(p + 1, e - p - 1); }
    auto e = j.find_first_of(",}\r\n", p); return j.substr(p, e - p);
}
static int jget_int(const std::string& j, const std::string& key, int def_val) {
    std::string s = jget(j, key);
    if (s.empty()) return def_val;
    try { return std::stoi(s); } catch (...) { return def_val; }
}
static float jget_float(const std::string& j, const std::string& key, float def_val) {
    std::string s = jget(j, key);
    if (s.empty()) return def_val;
    try { return std::stof(s); } catch (...) { return def_val; }
}

// ---------------------------------------------------------------- SHA-256 (BCrypt, in-process)
static bool sha256_file(const std::string& path, std::string& hex, std::string& err) {
    BCRYPT_ALG_HANDLE alg = nullptr; BCRYPT_HASH_HANDLE h = nullptr; NTSTATUS st;
    if ((st = BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0)) < 0) {
        char b[48]; std::snprintf(b, sizeof b, "BCryptOpenAlgorithmProvider NTSTATUS 0x%08lX", (unsigned long)st); err = b; return false; }
    if ((st = BCryptCreateHash(alg, &h, nullptr, 0, nullptr, 0, 0)) < 0) {
        char b[48]; std::snprintf(b, sizeof b, "BCryptCreateHash NTSTATUS 0x%08lX", (unsigned long)st); err = b;
        BCryptCloseAlgorithmProvider(alg, 0); return false; }
    std::ifstream f(path, std::ios::binary);
    if (!f) { err = "open failed: " + path; BCryptDestroyHash(h); BCryptCloseAlgorithmProvider(alg, 0); return false; }
    std::vector<char> buf(1 << 20);
    while (f) {
        f.read(buf.data(), buf.size()); auto n = f.gcount();
        if (n > 0 && (st = BCryptHashData(h, (PUCHAR)buf.data(), (ULONG)n, 0)) < 0) {
            char b[48]; std::snprintf(b, sizeof b, "BCryptHashData NTSTATUS 0x%08lX", (unsigned long)st); err = b;
            BCryptDestroyHash(h); BCryptCloseAlgorithmProvider(alg, 0); return false; }
    }
    unsigned char d[32];
    st = BCryptFinishHash(h, d, sizeof d, 0);
    BCryptDestroyHash(h); BCryptCloseAlgorithmProvider(alg, 0);
    if (st < 0) { char b[48]; std::snprintf(b, sizeof b, "BCryptFinishHash NTSTATUS 0x%08lX", (unsigned long)st); err = b; return false; }
    static const char* x = "0123456789abcdef"; hex.clear();
    for (unsigned char c : d) { hex += x[c >> 4]; hex += x[c & 15]; }
    return true;
}

// ---------------------------------------------------------------- GPU state (NVML, in-process)
static std::string gpu_state(unsigned idx = 0) {
    nvmlReturn_t r = nvmlInit_v2();
    if (r != NVML_SUCCESS) return std::string("ERROR nvmlInit_v2: ") + nvmlErrorString(r);
    std::ostringstream o; nvmlDevice_t d;
    if ((r = nvmlDeviceGetHandleByIndex_v2(idx, &d)) != NVML_SUCCESS) {
        nvmlShutdown(); return std::string("ERROR nvmlDeviceGetHandleByIndex_v2: ") + nvmlErrorString(r); }
    char name[96] = {}, drv[96] = {};
    nvmlMemory_t mem{}; unsigned temp = 0; nvmlUtilization_t util{}; int maj = 0, min = 0;
    auto chk = [&](const char* w, nvmlReturn_t rr) { if (rr != NVML_SUCCESS) o << "ERROR " << w << ": " << nvmlErrorString(rr) << "; "; };
    chk("nvmlDeviceGetName", nvmlDeviceGetName(d, name, sizeof name));
    chk("nvmlSystemGetDriverVersion", nvmlSystemGetDriverVersion(drv, sizeof drv));
    chk("nvmlDeviceGetMemoryInfo", nvmlDeviceGetMemoryInfo(d, &mem));
    chk("nvmlDeviceGetTemperature", nvmlDeviceGetTemperature(d, NVML_TEMPERATURE_GPU, &temp));
    chk("nvmlDeviceGetUtilizationRates", nvmlDeviceGetUtilizationRates(d, &util));
    chk("nvmlDeviceGetCudaComputeCapability", nvmlDeviceGetCudaComputeCapability(d, &maj, &min));
    o << name << ", " << drv << ", " << (mem.total >> 20) << " MiB, " << (mem.used >> 20) << " MiB, "
      << temp << ", " << util.gpu << " %, " << maj << "." << min;
    nvmlShutdown();
    return o.str();
}

// ---------------------------------------------------------------- BGR24 Visual Overlay Primitives
static void draw_rect(unsigned char* bgr, int w, int h, int x0, int y0, int x1, int y1, unsigned char b, unsigned char g, unsigned char r) {
    x0 = std::max(0, std::min(w - 1, x0)); x1 = std::max(0, std::min(w - 1, x1));
    y0 = std::max(0, std::min(h - 1, y0)); y1 = std::max(0, std::min(h - 1, y1));
    for (int y = y0; y <= y1; ++y) {
        for (int x = x0; x <= x1; ++x) {
            int idx = (y * w + x) * 3;
            bgr[idx + 0] = b; bgr[idx + 1] = g; bgr[idx + 2] = r;
        }
    }
}
static void draw_box(unsigned char* bgr, int w, int h, int x0, int y0, int x1, int y1, int thick, unsigned char b, unsigned char g, unsigned char r) {
    for (int t = 0; t < thick; ++t) {
        for (int x = x0 - t; x <= x1 + t; ++x) {
            if (x >= 0 && x < w) {
                if (y0 - t >= 0 && y0 - t < h) { int i = ((y0 - t) * w + x) * 3; bgr[i] = b; bgr[i+1] = g; bgr[i+2] = r; }
                if (y1 + t >= 0 && y1 + t < h) { int i = ((y1 + t) * w + x) * 3; bgr[i] = b; bgr[i+1] = g; bgr[i+2] = r; }
            }
        }
        for (int y = y0 - t; y <= y1 + t; ++y) {
            if (y >= 0 && y < h) {
                if (x0 - t >= 0 && x0 - t < w) { int i = (y * w + (x0 - t)) * 3; bgr[i] = b; bgr[i+1] = g; bgr[i+2] = r; }
                if (x1 + t >= 0 && x1 + t < w) { int i = (y * w + (x1 + t)) * 3; bgr[i] = b; bgr[i+1] = g; bgr[i+2] = r; }
            }
        }
    }
}
static void draw_line(unsigned char* bgr, int w, int h, int x0, int y0, int x1, int y1, unsigned char b, unsigned char g, unsigned char r) {
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy;
    while (true) {
        if (x0 >= 0 && x0 < w && y0 >= 0 && y0 < h) {
            int idx = (y0 * w + x0) * 3;
            bgr[idx + 0] = b; bgr[idx + 1] = g; bgr[idx + 2] = r;
        }
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}
static void draw_reticle(unsigned char* bgr, int w, int h, int cx, int cy, int radius, int thick, unsigned char b, unsigned char g, unsigned char r) {
    draw_box(bgr, w, h, cx - radius, cy - radius, cx + radius, cy + radius, thick, b, g, r);
    // ticks
    for (int t = -thick/2; t <= thick/2; ++t) {
        for (int dx = -radius - 8; dx <= radius + 8; ++dx) {
            int x = cx + dx, y = cy + t;
            if (x >= 0 && x < w && y >= 0 && y < h && (dx < -radius || dx > radius)) {
                int i = (y * w + x) * 3; bgr[i] = b; bgr[i+1] = g; bgr[i+2] = r;
            }
        }
        for (int dy = -radius - 8; dy <= radius + 8; ++dy) {
            int x = cx + t, y = cy + dy;
            if (x >= 0 && x < w && y >= 0 && y < h && (dy < -radius || dy > radius)) {
                int i = (y * w + x) * 3; bgr[i] = b; bgr[i+1] = g; bgr[i+2] = r;
            }
        }
    }
    draw_rect(bgr, w, h, cx - 2, cy - 2, cx + 2, cy + 2, 255, 255, 255);
}

static bool save_jpg(const std::string& path, const std::vector<unsigned char>& bgr, int w, int h) {
    std::string cmd = "ffmpeg -y -hide_banner -loglevel error -f rawvideo -pix_fmt bgr24 -s " +
                      std::to_string(w) + "x" + std::to_string(h) + " -i - -vframes 1 \"" + path + "\"";
    FILE* fp = _popen(cmd.c_str(), "wb");
    if (!fp) return false;
    fwrite(bgr.data(), 1, bgr.size(), fp);
    _pclose(fp);
    return true;
}

// ---------------------------------------------------------------- Video Frame Streaming
struct VideoStreamer {
    bool is_pipe = false;
    bool is_synthetic = false;
    FILE* fp_in = nullptr;
    FILE* fp_out = nullptr;
    int width = 1080;
    int height = 1920;
    std::string err;

    bool open(const std::string& input_path, const std::string& out_mp4_path, int w, int h) {
        width = w; height = h;
        if (input_path == "synthetic") {
            is_synthetic = true;
            return true;
        }
        // Hardware NVDEC input pipe (BGR24)
        std::string in_cmd = "ffmpeg -y -hide_banner -loglevel error -hwaccel cuda -i \"" + input_path + "\" -f rawvideo -pix_fmt bgr24 -";
        fp_in = _popen(in_cmd.c_str(), "rb");
        if (!fp_in) { err = "failed to _popen NVDEC pipe for: " + input_path; return false; }

        // Hardware NVENC output pipe (H.264 MP4)
        if (!out_mp4_path.empty()) {
            std::string out_cmd = "ffmpeg -y -hide_banner -loglevel error -f rawvideo -pix_fmt bgr24 -s " +
                                  std::to_string(width) + "x" + std::to_string(height) +
                                  " -r 59.94 -i - -c:v h264_nvenc -pix_fmt yuv420p -b:v 12M \"" + out_mp4_path + "\"";
            fp_out = _popen(out_cmd.c_str(), "wb");
            if (!fp_out) { _pclose(fp_in); fp_in = nullptr; err = "failed to _popen NVENC pipe for: " + out_mp4_path; return false; }
        }
        is_pipe = true;
        return true;
    }

    bool read_frame(std::vector<unsigned char>& h_bgr, std::vector<unsigned char>& h_gray, int frame_idx) {
        size_t pixels = (size_t)width * height;
        size_t bgr_bytes = pixels * 3;
        h_bgr.resize(bgr_bytes);
        h_gray.resize(pixels);

        if (is_synthetic) {
            if (frame_idx >= 2) return false;
            std::fill(h_bgr.begin(), h_bgr.end(), 128);
            std::fill(h_gray.begin(), h_gray.end(), 128);
            int cx = 400 + (frame_idx == 1 ? 3 : 0);
            int cy = 300 + (frame_idx == 1 ? 2 : 0);
            for (int dy = -12; dy <= 12; ++dy) {
                for (int dx = -12; dx <= 12; ++dx) {
                    float r2 = (float)(dx*dx + dy*dy);
                    int val = (int)(255.0f * std::exp(-r2 / 18.0f));
                    if (cy + dy >= 0 && cy + dy < height && cx + dx >= 0 && cx + dx < width) {
                        int p = (cy + dy) * width + (cx + dx);
                        unsigned char c = (unsigned char)std::min(255, 128 + val);
                        h_gray[p] = c;
                        h_bgr[p*3 + 0] = c; h_bgr[p*3 + 1] = c; h_bgr[p*3 + 2] = c;
                    }
                }
            }
            return true;
        }

        size_t n = fread(h_bgr.data(), 1, bgr_bytes, fp_in);
        if (n != bgr_bytes) return false;

        // Fast integer luminance conversion for CUDA tracking kernel
        for (size_t i = 0; i < pixels; ++i) {
            h_gray[i] = (unsigned char)((h_bgr[i*3 + 0] * 29 + h_bgr[i*3 + 1] * 150 + h_bgr[i*3 + 2] * 77) >> 8);
        }
        return true;
    }

    void write_frame(const std::vector<unsigned char>& h_bgr) {
        if (fp_out) {
            fwrite(h_bgr.data(), 1, h_bgr.size(), fp_out);
        }
    }

    void close() {
        if (fp_in) { _pclose(fp_in); fp_in = nullptr; }
        if (fp_out) { _pclose(fp_out); fp_out = nullptr; }
    }

    ~VideoStreamer() { close(); }
};

// ---------------------------------------------------------------- Pin Specification
struct PinSpec {
    int idx = 0;
    std::string name;
    float init_x = 0;
    float init_y = 0;
    float curr_x = 0;
    float curr_y = 0;
    float min_conf = 1.0f;
    float max_conf = 0.0f;
    double sum_conf = 0.0;
    int locked_frames = 0;
    int drift_frames = 0;
    int lost_frames = 0;
    std::vector<std::pair<float, float>> trail;
};

static std::vector<PinSpec> parse_pins_json(const std::string& j, int w, int h) {
    std::vector<PinSpec> pins;
    auto pos = j.find("\"pins\"");
    if (pos != std::string::npos) {
        auto b_open = j.find('[', pos);
        auto b_close = j.find(']', b_open);
        if (b_open != std::string::npos && b_close != std::string::npos) {
            std::string sub = j.substr(b_open, b_close - b_open + 1);
            size_t cur = 0;
            int idx = 0;
            while ((cur = sub.find('{', cur)) != std::string::npos) {
                auto end_obj = sub.find('}', cur);
                if (end_obj == std::string::npos) break;
                std::string obj = sub.substr(cur, end_obj - cur + 1);
                std::string label = jget(obj, "label");
                if (label.empty()) label = jget(obj, "name");
                if (label.empty()) label = "pin_" + std::to_string(idx);
                float px = jget_float(obj, "x", 0.0f);
                float py = jget_float(obj, "y", 0.0f);
                PinSpec p;
                p.idx = idx++;
                p.name = label;
                p.init_x = px;
                p.init_y = py;
                p.curr_x = px;
                p.curr_y = py;
                pins.push_back(p);
                cur = end_obj + 1;
            }
        }
    }
    if (pins.empty()) {
        pins = {
            { 0, "pin_0", (float)w * 0.35f, (float)h * 0.35f, (float)w * 0.35f, (float)h * 0.35f },
            { 1, "pin_1", (float)w * 0.65f, (float)h * 0.65f, (float)w * 0.65f, (float)h * 0.65f }
        };
    }
    return pins;
}

// ---------------------------------------------------------------- ledger (DuckDB C API, in-process)
struct Ledger {
    duckdb_database db = nullptr; duckdb_connection con = nullptr; std::string err;
    bool open(const std::string& path) {
        char* oe = nullptr;
        if (duckdb_open_ext(path.c_str(), &db, nullptr, &oe) == DuckDBError) {
            err = std::string("duckdb_open_ext(") + path + "): " + (oe ? oe : "unknown");
            if (oe) duckdb_free(oe); return false; }
        if (duckdb_connect(db, &con) == DuckDBError) { err = "duckdb_connect failed"; return false; }
        return true;
    }
    ~Ledger() { if (con) duckdb_disconnect(&con); if (db) duckdb_close(&db); }

    bool exec(const std::string& sql, const std::vector<std::string>& params) {
        duckdb_prepared_statement ps;
        if (duckdb_prepare(con, sql.c_str(), &ps) == DuckDBError) {
            err = std::string("duckdb_prepare: ") + duckdb_prepare_error(ps); duckdb_destroy_prepare(&ps); return false; }
        for (idx_t i = 0; i < params.size(); ++i) {
            auto st = params[i].empty() ? duckdb_bind_null(ps, i + 1) : duckdb_bind_varchar(ps, i + 1, params[i].c_str());
            if (st == DuckDBError) { err = "duckdb_bind param " + std::to_string(i + 1); duckdb_destroy_prepare(&ps); return false; }
        }
        duckdb_result res;
        if (duckdb_execute_prepared(ps, &res) == DuckDBError) {
            err = std::string("duckdb_execute_prepared: ") + duckdb_result_error(&res);
            duckdb_destroy_result(&res); duckdb_destroy_prepare(&ps); return false; }
        duckdb_destroy_result(&res); duckdb_destroy_prepare(&ps); return true;
    }
    bool scalar(const std::string& sql, const std::string& p1, std::string& out, bool& found) {
        found = false; duckdb_prepared_statement ps;
        if (duckdb_prepare(con, sql.c_str(), &ps) == DuckDBError) {
            err = std::string("duckdb_prepare: ") + duckdb_prepare_error(ps); duckdb_destroy_prepare(&ps); return false; }
        duckdb_bind_varchar(ps, 1, p1.c_str());
        duckdb_result res;
        if (duckdb_execute_prepared(ps, &res) == DuckDBError) {
            err = std::string("duckdb_execute_prepared: ") + duckdb_result_error(&res);
            duckdb_destroy_result(&res); duckdb_destroy_prepare(&ps); return false; }
        if (duckdb_row_count(&res) > 0 && !duckdb_value_is_null(&res, 0, 0)) {
            char* v = duckdb_value_varchar(&res, 0, 0); out = v ? v : ""; if (v) duckdb_free(v); found = true; }
        duckdb_destroy_result(&res); duckdb_destroy_prepare(&ps); return true;
    }
};

// ---------------------------------------------------------------- run state
struct OutputItem {
    std::string output_id;
    std::string path;
    std::string kind;
    long long bytes = 0;
    std::string sha256;
};

struct Run {
    std::string run_id, run_dir, kernel_id, caller, subject, input, params_json, golden_id;
    std::string dll_path, dll_sha256, adapter_path, adapter_sha256, shape, symbol_init, symbol_main;
    std::string gpu_pre, gpu_post, timing_mode = "host_stream";
    std::string error_stage, error_trace;
    double t0 = 0, wall_ms = 0, gpu_ms = 0, vram_peak_mb = 0; long long frames = 0; bool ok = false;
    std::vector<OutputItem> outputs;
};

static bool write_manifest(const Run& R, const std::string& status) {
    std::ostringstream m;
    m << "{\n  \"schema\": \"kernel_lab.manifest/v1\",\n"
      << "  \"run_id\": " << json_s(R.run_id) << ", \"status\": " << json_s(status) << ",\n"
      << "  \"host_version\": " << json_s(HOST_VERSION) << ",\n"
      << "  \"kernel\": { \"kernel_id\": " << json_s(R.kernel_id) << ", \"dll_path\": " << json_s(R.dll_path)
      << ", \"dll_sha256\": " << json_s(R.dll_sha256) << ", \"shape\": " << json_s(R.shape)
      << ", \"symbol_init\": " << json_s(R.symbol_init) << ", \"symbol_main\": " << json_s(R.symbol_main)
      << ", \"adapter\": " << json_s(R.adapter_path) << ", \"adapter_sha256\": " << json_s(R.adapter_sha256) << " },\n"
      << "  \"invocation\": { \"caller\": " << json_s(R.caller) << ", \"subject\": " << json_s(R.subject)
      << ", \"params\": " << (R.params_json.empty() ? "{}" : R.params_json) << ", \"golden_id\": " << json_s(R.golden_id) << " },\n"
      << "  \"input\": { \"path\": " << json_s(R.input) << " },\n"
      << "  \"gpu\": { \"pre\": " << json_s(R.gpu_pre) << ", \"post\": " << json_s(R.gpu_post) << " },\n"
      << "  \"timing\": { \"wall_ms\": " << R.wall_ms << ", \"gpu_ms\": " << R.gpu_ms
      << ", \"timing_mode\": " << json_s(R.timing_mode) << " },\n"
      << "  \"memory\": { \"vram_peak_mb\": " << R.vram_peak_mb << " },\n"
      << "  \"frames\": " << R.frames << ",\n"
      << "  \"outputs\": [";
    for (size_t i = 0; i < R.outputs.size(); ++i) {
        if (i > 0) m << ", ";
        m << "{ \"path\": " << json_s(R.outputs[i].path)
          << ", \"kind\": " << json_s(R.outputs[i].kind)
          << ", \"bytes\": " << R.outputs[i].bytes
          << ", \"sha256\": " << json_s(R.outputs[i].sha256) << " }";
    }
    m << "],\n"
      << "  \"error\": { \"stage\": " << json_s(R.error_stage) << ", \"trace\": " << json_s(R.error_trace) << " }\n}\n";
    return write_file(R.run_dir + "\\manifest.json", m.str());
}

static const char* SQL_STARTED =
    "INSERT INTO run_events (event_id, run_id, event, kernel_id, dll_path, dll_sha256, symbol, adapter_sha256, caller, subject,"
    " input_path, params_json, golden_id, run_dir, host_version, gpu_state_pre) VALUES (?,?,'started',?,?,?,?,?,?,?,?,?,?,?,?,?)";
static const char* SQL_TERMINAL =
    "INSERT INTO run_events (event_id, run_id, event, ok, gpu_ms, wall_ms, vram_peak_mb, frames, timing_mode,"
    " error_stage, error_trace, gpu_state_post) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)";
static const char* SQL_OUTPUT =
    "INSERT INTO outputs (output_id, run_id, path, kind, bytes, sha256) VALUES (?,?,?,?,?,?)";

typedef int (*fn_void_t)();
static int seh_call_void(fn_void_t f, DWORD* exc) {
    __try { return f(); }
    __except (*exc = GetExceptionCode(), EXCEPTION_EXECUTE_HANDLER) { return INT_MIN; }
}

typedef int (*fn_geopin_extract_patches_t)(
    const unsigned char* d_frame_gray,
    int width, int height, int pitch,
    const float* h_pin_x, const float* h_pin_y,
    int num_pins, int patch_radius,
    float* d_out_patches
);
typedef int (*fn_geopin_track_step_t)(
    const unsigned char* d_curr_gray,
    int width, int height, int pitch,
    const float* d_template_patches,
    const float* in_pin_x, const float* in_pin_y,
    float* out_pin_x, float* out_pin_y,
    float* out_confidence, int* out_status,
    int num_pins, int patch_radius, int search_radius
);

static void usage() {
    std::fprintf(stderr,
        "kernel_host.exe --kernel <kernel_id> --input <path> --caller <name> --subject <name>\n"
        "                [--params <json-file>] [--golden <golden_id>] [--lab <dir>]\n"
        "  or: kernel_host.exe --verdict <val> --run <run_id> [--note <text>] [--source <name>]\n");
}

int main(int argc, char** argv) {
    std::string lab = "c:\\dev\\kernel_lab", params_file; Run R;
    std::string verdict_val, verdict_run_id, verdict_note, verdict_source = "operator";
    for (int i = 1; i + 1 < argc; i += 2) {
        std::string k = argv[i], v = argv[i + 1];
        if (k == "--verdict") verdict_val = v;
        else if (k == "--run") verdict_run_id = v;
        else if (k == "--note") verdict_note = v;
        else if (k == "--source") verdict_source = v;
        else if (k == "--kernel") R.kernel_id = v;
        else if (k == "--input") R.input = v;
        else if (k == "--caller") R.caller = v;
        else if (k == "--subject") R.subject = v;
        else if (k == "--params") params_file = v;
        else if (k == "--golden") R.golden_id = v;
        else if (k == "--lab") lab = v;
    }

    // Verdict logging branch
    if (!verdict_val.empty()) {
        if (verdict_run_id.empty()) {
            std::fprintf(stderr, "Error: --verdict requires --run <run_id>\n");
            return 2;
        }
        Ledger L;
        if (!L.open(lab + "\\kernel_lab.duckdb")) {
            std::fprintf(stderr, "stage=ledger %s\n", L.err.c_str());
            return 3;
        }
        std::string v_id = verdict_run_id + "_v_" + now_local("%Y%m%dT%H%M%S");
        const char* SQL_VERDICT = "INSERT INTO verdicts (verdict_id, run_id, ts, verdict, note, source) VALUES (?, ?, now(), ?, ?, ?)";
        if (!L.exec(SQL_VERDICT, { v_id, verdict_run_id, verdict_val, verdict_note, verdict_source })) {
            std::fprintf(stderr, "stage=ledger %s\n", L.err.c_str());
            return 3;
        }
        std::printf("{\"verdict_id\":%s,\"run_id\":%s,\"verdict\":%s,\"note\":%s,\"status\":\"recorded\"}\n",
            json_s(v_id).c_str(), json_s(verdict_run_id).c_str(), json_s(verdict_val).c_str(), json_s(verdict_note).c_str());
        return 0;
    }

    if (R.kernel_id.empty() || R.input.empty() || R.caller.empty() || R.subject.empty()) { usage(); return 2; }
    R.t0 = qpc_ms();
    if (!params_file.empty() && !read_file(params_file, R.params_json)) {
        std::fprintf(stderr, "stage=resolve params file unreadable: %s\n", params_file.c_str()); return 2; }

    Ledger L;
    if (!L.open(lab + "\\kernel_lab.duckdb")) { std::fprintf(stderr, "stage=ledger %s\n", L.err.c_str()); return 3; }

    // ---- run_id + folder first
    std::string stamp = now_local("%Y%m%dT%H%M%S");
    bool made = false;
    for (int seq = 1; seq < 1000 && !made; ++seq) {
        char b[8]; std::snprintf(b, sizeof b, "%03d", seq);
        R.run_id = stamp + "_" + R.kernel_id + "_" + b;
        R.run_dir = lab + "\\runs\\" + R.run_id;
        std::error_code ec; made = fs::create_directories(R.run_dir + "\\outputs", ec);
        if (ec) { std::fprintf(stderr, "stage=resolve create_directories(%s): %s\n", R.run_dir.c_str(), ec.message().c_str()); return 3; }
    }

    auto finish = [&](const std::string& ev) -> int {
        R.gpu_post = gpu_state();
        R.wall_ms = qpc_ms() - R.t0;
        write_manifest(R, ev);
        char g[32], w[32], v[32], f[32];
        std::snprintf(g, sizeof g, "%.6f", R.gpu_ms); std::snprintf(w, sizeof w, "%.6f", R.wall_ms);
        std::snprintf(v, sizeof v, "%.3f", R.vram_peak_mb); std::snprintf(f, sizeof f, "%lld", R.frames);
        if (!L.exec(SQL_TERMINAL, { R.run_id + ":" + ev, R.run_id, ev, R.ok ? "true" : "false", g, w, v, f,
                                    R.timing_mode, R.error_stage, R.error_trace, R.gpu_post })) {
            write_file(R.run_dir + "\\stderr.log", "stage=ledger\n" + L.err + "\n");
            std::fprintf(stderr, "stage=ledger %s\n", L.err.c_str());
        }
        for (const auto& out : R.outputs) {
            L.exec(SQL_OUTPUT, { out.output_id, R.run_id, out.path, out.kind, std::to_string(out.bytes), out.sha256 });
        }
        std::printf("{\"run_id\":%s,\"ok\":%s,\"gpu_ms\":%s,\"wall_ms\":%s,\"run_dir\":%s,\"outputs\":%zu,\"error_stage\":%s,\"error_trace\":%s}\n",
            json_s(R.run_id).c_str(), R.ok ? "true" : "false", g, w, json_s(R.run_dir).c_str(), R.outputs.size(),
            json_s(R.error_stage).c_str(), json_s(R.error_trace).c_str());
        return R.ok ? 0 : 1;
    };
    auto fail = [&](const std::string& stage, const std::string& trace) {
        R.ok = false; R.error_stage = stage; R.error_trace = trace;
        write_file(R.run_dir + "\\stderr.log", "stage=" + stage + "\n" + trace + "\n");
        return finish("failed");
    };

    // ---- resolve
    std::string resolve_err, herr;
    bool found = false;
    if (!L.scalar("SELECT dll_path FROM kernels WHERE kernel_id = ?", R.kernel_id, R.dll_path, found))
        resolve_err = "registry query failed: " + L.err;
    else if (!found) resolve_err = "kernel_id not in registry or dll_path NULL: " + R.kernel_id;
    R.adapter_path = lab + "\\host\\adapters\\" + R.kernel_id + ".json";
    std::string adapter;
    if (resolve_err.empty() && !read_file(R.adapter_path, adapter)) resolve_err = "adapter missing: " + R.adapter_path;
    if (resolve_err.empty() && !sha256_file(R.dll_path, R.dll_sha256, herr)) resolve_err = "dll sha256: " + herr;
    if (resolve_err.empty() && !sha256_file(R.adapter_path, R.adapter_sha256, herr)) resolve_err = "adapter sha256: " + herr;
    if (!adapter.empty()) {
        R.shape = jget(adapter, "shape"); R.symbol_init = jget(adapter, "symbol_init"); R.symbol_main = jget(adapter, "symbol_main");
        std::string tm = jget(adapter, "timing_mode"); if (!tm.empty()) R.timing_mode = tm;
    }

    // ---- started event
    R.gpu_pre = gpu_state();
    write_file(R.run_dir + "\\gpu_state_pre.txt", R.gpu_pre + "\n");
    write_manifest(R, "started");
    if (!L.exec(SQL_STARTED, { R.run_id + ":started", R.run_id, R.kernel_id, R.dll_path, R.dll_sha256, R.symbol_main,
                               R.adapter_sha256, R.caller, R.subject, R.input, R.params_json, R.golden_id, R.run_dir,
                               HOST_VERSION, R.gpu_pre })) {
        write_file(R.run_dir + "\\stderr.log", "stage=ledger\n" + L.err + "\n");
        std::fprintf(stderr, "stage=ledger %s\n", L.err.c_str());
        return 3;
    }
    if (!resolve_err.empty()) return fail("resolve", resolve_err);

    // ---- load
    std::wstring wdll(R.dll_path.begin(), R.dll_path.end());
    HMODULE h = LoadLibraryExW(wdll.c_str(), nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    if (!h) return fail("load", "LoadLibraryExW(" + R.dll_path + "): " + win_err(GetLastError()));

    // ---- symbol
    std::map<std::string, FARPROC> sym;
    for (const std::string& s : { R.symbol_init, R.symbol_main }) {
        if (s.empty()) continue;
        FARPROC p = GetProcAddress(h, s.c_str());
        if (!p) return fail("symbol", "GetProcAddress(" + s + ") in " + R.dll_path + ": " + win_err(GetLastError()));
        sym[s] = p;
    }

    if (R.shape == "init_only") {
        if (R.symbol_init.empty()) return fail("resolve", "adapter has no symbol_init");
        cudaEvent_t e0, e1; cudaEventCreate(&e0); cudaEventCreate(&e1);
        cudaEventRecord(e0, 0);
        DWORD exc = 0;
        int rc = seh_call_void((fn_void_t)sym[R.symbol_init], &exc);
        cudaEventRecord(e1, 0);
        cudaEventSynchronize(e1);
        if (exc) { char b[64]; std::snprintf(b, sizeof b, "SEH exception 0x%08lX in ", exc); return fail("crash", b + R.symbol_init); }
        if (rc != 0) return fail("kernel_return", R.symbol_init + " returned " + std::to_string(rc));
        float ms = 0; cudaEventElapsedTime(&ms, e0, e1); R.gpu_ms = ms;
        R.ok = true; return finish("finished");
    }

    // ---- Shape: init_step_release (cu_geopin_solver)
    if (R.kernel_id == "cu_geopin_solver") {
        FARPROC p_extract = GetProcAddress(h, "cu_geopin_extract_patches");
        if (!p_extract) return fail("symbol", "GetProcAddress(cu_geopin_extract_patches): " + win_err(GetLastError()));
        auto fn_extract = (fn_geopin_extract_patches_t)p_extract;
        auto fn_track = (fn_geopin_track_step_t)sym[R.symbol_main];

        int width = jget_int(R.params_json, "width", (R.input == "synthetic" ? 1920 : 1080));
        int height = jget_int(R.params_json, "height", (R.input == "synthetic" ? 1080 : 1920));
        int max_frames = jget_int(R.params_json, "max_frames", (R.input == "synthetic" ? 2 : 120));
        int patch_radius = jget_int(R.params_json, "patch_radius", 10);
        int search_radius = jget_int(R.params_json, "search_radius", 24);

        std::vector<PinSpec> pins = parse_pins_json(R.params_json, width, height);
        int num_pins = (int)pins.size();

        std::string out_video_path = (R.input == "synthetic") ? "" : (R.run_dir + "\\outputs\\tracked.mp4");

        VideoStreamer streamer;
        if (!streamer.open(R.input, out_video_path, width, height)) {
            return fail("input", streamer.err);
        }

        // Read Frame 0
        std::vector<unsigned char> h_bgr, h_gray;
        if (!streamer.read_frame(h_bgr, h_gray, 0)) {
            return fail("input", "failed to read frame 0 from: " + R.input);
        }

        unsigned char* d_frame = nullptr;
        float* d_templates = nullptr;
        size_t frame_bytes = (size_t)width * height;
        int diam = 2 * patch_radius + 1;
        size_t patch_bytes = (size_t)num_pins * diam * diam * sizeof(float);

        cudaError_t ce;
        if ((ce = cudaMalloc((void**)&d_frame, frame_bytes)) != cudaSuccess) return fail("cuda", cuda_err("cudaMalloc(d_frame)", ce));
        if ((ce = cudaMalloc((void**)&d_templates, patch_bytes)) != cudaSuccess) { cudaFree(d_frame); return fail("cuda", cuda_err("cudaMalloc(d_templates)", ce)); }

        cudaMemcpy(d_frame, h_gray.data(), frame_bytes, cudaMemcpyHostToDevice);

        std::vector<float> pin_x(num_pins), pin_y(num_pins);
        for (int p = 0; p < num_pins; ++p) {
            pin_x[p] = pins[p].init_x; pin_y[p] = pins[p].init_y;
            pins[p].trail.push_back({ pins[p].init_x, pins[p].init_y });
        }

        cudaEvent_t e0, e1; cudaEventCreate(&e0); cudaEventCreate(&e1);
        size_t free0 = 0, free1 = 0, total = 0;
        cudaMemGetInfo(&free0, &total);

        // Step 1: Init
        seh_call_void((fn_void_t)sym[R.symbol_init], nullptr);

        // Step 2: Extract template patches on frame 0
        int r_ext = fn_extract(d_frame, width, height, width, pin_x.data(), pin_y.data(), num_pins, patch_radius, d_templates);
        if (r_ext != 0) {
            cudaFree(d_frame); cudaFree(d_templates);
            return fail("kernel_return", "cu_geopin_extract_patches returned " + std::to_string(r_ext));
        }

        // Render Frame 0 HUD
        if (!out_video_path.empty()) {
            draw_rect(h_bgr.data(), width, height, 10, 10, width - 10, 60, 20, 11, 7);
            draw_line(h_bgr.data(), width, height, 10, 10, width - 10, 10, 255, 229, 0);
            draw_line(h_bgr.data(), width, height, 10, 60, width - 10, 60, 255, 229, 0);
            for (int p = 0; p < num_pins; ++p) {
                draw_reticle(h_bgr.data(), width, height, (int)pin_x[p], (int)pin_y[p], patch_radius + 2, 2, 0, 255, 0);
            }
            streamer.write_frame(h_bgr);
        }

        // Step 3: Continuous tracking loop
        std::vector<float> in_x = pin_x, in_y = pin_y;
        std::vector<float> out_x(num_pins), out_y(num_pins), out_conf(num_pins);
        std::vector<int> out_status(num_pins);

        struct FrameStep {
            int frame;
            std::vector<float> x;
            std::vector<float> y;
            std::vector<float> conf;
            std::vector<int> status;
        };
        std::vector<FrameStep> timeline;

        cudaEventRecord(e0, 0);

        int processed_frames = 1;
        for (int f = 1; f < max_frames; ++f) {
            if (!streamer.read_frame(h_bgr, h_gray, f)) break;
            cudaMemcpy(d_frame, h_gray.data(), frame_bytes, cudaMemcpyHostToDevice);

            int r_trk = fn_track(d_frame, width, height, width, d_templates,
                                 in_x.data(), in_y.data(),
                                 out_x.data(), out_y.data(),
                                 out_conf.data(), out_status.data(),
                                 num_pins, patch_radius, search_radius);
            if (r_trk != 0) {
                cudaFree(d_frame); cudaFree(d_templates);
                return fail("kernel_return", "cu_geopin_track_step failed at frame " + std::to_string(f) + " rc=" + std::to_string(r_trk));
            }

            FrameStep step;
            step.frame = f; step.x = out_x; step.y = out_y; step.conf = out_conf; step.status = out_status;
            timeline.push_back(step);

            for (int p = 0; p < num_pins; ++p) {
                pins[p].curr_x = out_x[p];
                pins[p].curr_y = out_y[p];
                pins[p].trail.push_back({ out_x[p], out_y[p] });
                float c = out_conf[p];
                if (c < pins[p].min_conf) pins[p].min_conf = c;
                if (c > pins[p].max_conf) pins[p].max_conf = c;
                pins[p].sum_conf += c;
                if (out_status[p] == 1) pins[p].locked_frames++;
                else if (out_status[p] == 2) pins[p].drift_frames++;
                else pins[p].lost_frames++;
            }

            // Render HUD onto BGR frame
            if (!out_video_path.empty()) {
                // Top status bar
                draw_rect(h_bgr.data(), width, height, 10, 10, width - 10, 60, 20, 11, 7);
                draw_line(h_bgr.data(), width, height, 10, 10, width - 10, 10, 255, 229, 0);
                draw_line(h_bgr.data(), width, height, 10, 60, width - 10, 60, 255, 229, 0);

                // Draw wireframe connecting pins
                if (num_pins >= 2) {
                    for (int i = 0; i < num_pins; ++i) {
                        for (int j = i + 1; j < num_pins; ++j) {
                            draw_line(h_bgr.data(), width, height, (int)out_x[i], (int)out_y[i], (int)out_x[j], (int)out_y[j], 255, 229, 0);
                        }
                    }
                }

                // Draw trails and reticles
                for (int p = 0; p < num_pins; ++p) {
                    const auto& tr = pins[p].trail;
                    size_t start_k = tr.size() > 40 ? tr.size() - 40 : 0;
                    for (size_t k = start_k; k + 1 < tr.size(); ++k) {
                        draw_line(h_bgr.data(), width, height, (int)tr[k].first, (int)tr[k].second, (int)tr[k+1].first, (int)tr[k+1].second, 0, 230, 118);
                    }
                    unsigned char col_b = (out_status[p] == 1) ? 0 : 0;
                    unsigned char col_g = (out_status[p] == 1) ? 255 : 50;
                    unsigned char col_r = (out_status[p] == 1) ? 0 : 255;
                    draw_reticle(h_bgr.data(), width, height, (int)out_x[p], (int)out_y[p], patch_radius + 2, 2, col_b, col_g, col_r);
                }
                streamer.write_frame(h_bgr);
            }

            in_x = out_x; in_y = out_y;
            processed_frames++;
        }

        cudaEventRecord(e1, 0);
        cudaEventSynchronize(e1);
        float ms = 0; cudaEventElapsedTime(&ms, e0, e1);
        R.gpu_ms = ms;
        cudaMemGetInfo(&free1, &total);
        R.vram_peak_mb = free0 > free1 ? (double)(free0 - free1) / (1024.0 * 1024.0) : 0.0;

        cudaFree(d_frame); cudaFree(d_templates);
        streamer.close();

        // Register tracked.mp4 output if generated
        if (!out_video_path.empty() && fs::exists(out_video_path)) {
            std::string video_sha;
            sha256_file(out_video_path, video_sha, herr);
            OutputItem oi_v;
            oi_v.output_id = R.run_id + "_tracked_mp4";
            oi_v.path = "outputs/tracked.mp4";
            oi_v.kind = "video";
            oi_v.bytes = (long long)fs::file_size(out_video_path);
            oi_v.sha256 = video_sha;
            R.outputs.push_back(oi_v);
        }

        // Write outputs/track.json
        std::ostringstream tj;
        tj << "{\n  \"kernel_id\": \"cu_geopin_solver\",\n"
           << "  \"input\": " << json_s(R.input) << ",\n"
           << "  \"golden_id\": " << json_s(R.golden_id) << ",\n"
           << "  \"dimensions\": { \"width\": " << width << ", \"height\": " << height << " },\n"
           << "  \"frames_processed\": " << processed_frames << ",\n"
           << "  \"num_pins\": " << num_pins << ",\n"
           << "  \"pins\": [\n";
        for (int p = 0; p < num_pins; ++p) {
            if (p > 0) tj << ",\n";
            int steps = std::max(1, processed_frames - 1);
            float mean_c = (float)(pins[p].sum_conf / (double)steps);
            tj << "    { \"idx\": " << pins[p].idx << ", \"name\": " << json_s(pins[p].name)
               << ", \"init_x\": " << pins[p].init_x << ", \"init_y\": " << pins[p].init_y
               << ", \"final_x\": " << pins[p].curr_x << ", \"final_y\": " << pins[p].curr_y
               << ", \"min_confidence\": " << pins[p].min_conf << ", \"max_confidence\": " << pins[p].max_conf
               << ", \"mean_confidence\": " << mean_c
               << ", \"locked_frames\": " << pins[p].locked_frames
               << ", \"drift_frames\": " << pins[p].drift_frames
               << ", \"lost_frames\": " << pins[p].lost_frames << " }";
        }
        tj << "\n  ],\n  \"timeline_samples\": [\n";
        int stride = processed_frames > 60 ? 5 : 1;
        bool first_step = true;
        for (size_t i = 0; i < timeline.size(); i += stride) {
            if (!first_step) tj << ",\n";
            first_step = false;
            tj << "    { \"frame\": " << timeline[i].frame << ", \"pins\": [";
            for (int p = 0; p < num_pins; ++p) {
                if (p > 0) tj << ", ";
                tj << "{ \"x\": " << timeline[i].x[p] << ", \"y\": " << timeline[i].y[p]
                   << ", \"conf\": " << timeline[i].conf[p] << ", \"status\": " << timeline[i].status[p] << " }";
            }
            tj << "] }";
        }
        tj << "\n  ]\n}\n";

        std::string track_path = R.run_dir + "\\outputs\\track.json";
        write_file(track_path, tj.str());

        std::string track_sha;
        sha256_file(track_path, track_sha, herr);
        OutputItem oi;
        oi.output_id = R.run_id + "_track_json";
        oi.path = "outputs/track.json";
        oi.kind = "telemetry_json";
        oi.bytes = (long long)tj.str().size();
        oi.sha256 = track_sha;
        R.outputs.push_back(oi);

        R.frames = processed_frames;
        R.ok = true;
        return finish("finished");
    }

    // ---- Shape: init_step_release (adaptive_delta_fused)
    if (R.kernel_id == "adaptive_delta_fused") {
        FARPROC p_init = sym[R.symbol_init];
        FARPROC p_main = sym[R.symbol_main];
        if (!p_init) return fail("symbol", "Missing symbol_init: " + R.symbol_init);
        if (!p_main) return fail("symbol", "Missing symbol_main: " + R.symbol_main);

        typedef int (*fn_screen_init_t)(int width, int height);
        typedef int (*fn_adaptive_delta_fused_t)(
            const unsigned char* d_curr_bgra,
            float* d_out_rgb_chw,
            uint32_t* h_out_bitmask,
            int width, int height, int pitch,
            float mse_threshold,
            int* out_mutated_tile_count
        );
        auto fn_init = (fn_screen_init_t)p_init;
        auto fn_delta = (fn_adaptive_delta_fused_t)p_main;

        int width = jget_int(R.params_json, "width", (R.input == "synthetic" ? 1920 : 1080));
        int height = jget_int(R.params_json, "height", (R.input == "synthetic" ? 1080 : 1920));
        int max_frames = jget_int(R.params_json, "max_frames", (R.input == "synthetic" ? 2 : 120));
        float mse_threshold = jget_float(R.params_json, "mse_threshold", 10.0f);

        int tiles_x = (width + 15) / 16;
        int tiles_y = (height + 15) / 16;
        int total_tiles = tiles_x * tiles_y;
        int num_words = (total_tiles + 31) / 32;
        size_t bitmask_bytes = (size_t)num_words * sizeof(uint32_t);
        size_t bgra_bytes = (size_t)width * height * 4;

        int init_rc = fn_init(width, height);
        if (init_rc != 0) return fail("kernel_init", "cu_init_screen_engine returned " + std::to_string(init_rc));

        std::string out_video_path = (R.input == "synthetic") ? "" : (R.run_dir + "\\outputs\\delta_visualized.mp4");
        VideoStreamer streamer;
        if (!streamer.open(R.input, out_video_path, width, height)) {
            return fail("input", streamer.err);
        }

        unsigned char* d_curr_bgra = nullptr;
        cudaError_t ce = cudaMalloc((void**)&d_curr_bgra, bgra_bytes);
        if (ce != cudaSuccess) return fail("cuda", cuda_err("cudaMalloc(d_curr_bgra)", ce));

        std::vector<uint32_t> h_bitmask(num_words, 0);
        std::vector<unsigned char> h_bgr, h_gray, h_bgra(bgra_bytes);

        cudaEvent_t e0, e1; cudaEventCreate(&e0); cudaEventCreate(&e1);
        size_t free0 = 0, free1 = 0, total = 0;
        cudaMemGetInfo(&free0, &total);

        // Pre-fill frame 0
        if (R.input == "synthetic") {
            std::fill(h_bgra.begin(), h_bgra.end(), 128);
        } else {
            if (!streamer.read_frame(h_bgr, h_gray, 0)) {
                cudaFree(d_curr_bgra);
                return fail("input", "failed to read frame 0 from: " + R.input);
            }
            for (int i = 0; i < width * height; ++i) {
                h_bgra[i * 4 + 0] = h_bgr[i * 3 + 0];
                h_bgra[i * 4 + 1] = h_bgr[i * 3 + 1];
                h_bgra[i * 4 + 2] = h_bgr[i * 3 + 2];
                h_bgra[i * 4 + 3] = 255;
            }
        }
        cudaMemcpy(d_curr_bgra, h_bgra.data(), bgra_bytes, cudaMemcpyHostToDevice);

        int init_mutated = 0;
        fn_delta(d_curr_bgra, nullptr, h_bitmask.data(), width, height, width * 4, mse_threshold, &init_mutated);

        if (!out_video_path.empty()) {
            draw_rect(h_bgr.data(), width, height, 10, 10, width - 10, 60, 20, 11, 7);
            streamer.write_frame(h_bgr);
        }

        struct DeltaStep {
            int frame;
            int mutated_tiles;
            float mutated_pct;
        };
        std::vector<DeltaStep> timeline;
        timeline.push_back({ 0, init_mutated, (float)init_mutated / (float)total_tiles * 100.0f });

        int processed_frames = 1;
        int max_mutated_frame = 0;
        int max_mutated_count = 0;
        std::vector<unsigned char> best_preview_bgr;
        if (!h_bgr.empty()) best_preview_bgr = h_bgr;

        cudaEventRecord(e0, 0);

        for (int f = 1; f < max_frames; ++f) {
            if (R.input == "synthetic") {
                if (f >= 2) break;
                std::fill(h_bgra.begin(), h_bgra.end(), 128);
                // Mutate a 200x200 patch in frame 1
                for (int y = 200; y < 400; ++y) {
                    for (int x = 200; x < 400; ++x) {
                        int idx = (y * width + x) * 4;
                        h_bgra[idx + 0] = 255; h_bgra[idx + 1] = 0; h_bgra[idx + 2] = 0; h_bgra[idx + 3] = 255;
                    }
                }
            } else {
                if (!streamer.read_frame(h_bgr, h_gray, f)) break;
                for (int i = 0; i < width * height; ++i) {
                    h_bgra[i * 4 + 0] = h_bgr[i * 3 + 0];
                    h_bgra[i * 4 + 1] = h_bgr[i * 3 + 1];
                    h_bgra[i * 4 + 2] = h_bgr[i * 3 + 2];
                    h_bgra[i * 4 + 3] = 255;
                }
            }

            cudaMemcpy(d_curr_bgra, h_bgra.data(), bgra_bytes, cudaMemcpyHostToDevice);

            int mutated_tiles = 0;
            int rc = fn_delta(d_curr_bgra, nullptr, h_bitmask.data(), width, height, width * 4, mse_threshold, &mutated_tiles);
            if (rc != 0) {
                cudaFree(d_curr_bgra);
                return fail("kernel_return", "cu_adaptive_delta_fused returned " + std::to_string(rc));
            }

            float pct = (float)mutated_tiles / (float)total_tiles * 100.0f;
            timeline.push_back({ f, mutated_tiles, pct });

            if (mutated_tiles > max_mutated_count && !h_bgr.empty()) {
                max_mutated_count = mutated_tiles;
                max_mutated_frame = f;
            }

            // Draw bounding boxes around mutated 16x16 tiles
            if (!out_video_path.empty()) {
                for (int ty = 0; ty < tiles_y; ++ty) {
                    for (int tx = 0; tx < tiles_x; ++tx) {
                        int tile_idx = ty * tiles_x + tx;
                        int word = tile_idx / 32;
                        int bit = tile_idx % 32;
                        if ((h_bitmask[word] >> bit) & 1) {
                            int x0 = tx * 16;
                            int y0 = ty * 16;
                            int x1 = std::min(width - 1, x0 + 15);
                            int y1 = std::min(height - 1, y0 + 15);
                            draw_box(h_bgr.data(), width, height, x0, y0, x1, y1, 1, 0, 230, 118);
                        }
                    }
                }
                draw_rect(h_bgr.data(), width, height, 10, 10, width - 10, 60, 20, 11, 7);
                if (f == max_mutated_frame) best_preview_bgr = h_bgr;
                streamer.write_frame(h_bgr);
            }

            processed_frames++;
        }

        cudaEventRecord(e1, 0);
        cudaEventSynchronize(e1);
        float ms = 0; cudaEventElapsedTime(&ms, e0, e1);
        R.gpu_ms = ms;
        cudaMemGetInfo(&free1, &total);
        R.vram_peak_mb = free0 > free1 ? (double)(free0 - free1) / (1024.0 * 1024.0) : 0.0;

        cudaFree(d_curr_bgra);
        streamer.close();

        // Save preview JPEG if available
        if (!best_preview_bgr.empty()) {
            std::string preview_path = R.run_dir + "\\outputs\\preview_delta.jpg";
            if (save_jpg(preview_path, best_preview_bgr, width, height)) {
                std::string psha; sha256_file(preview_path, psha, herr);
                OutputItem oi_p;
                oi_p.output_id = R.run_id + "_preview_delta";
                oi_p.path = "outputs/preview_delta.jpg";
                oi_p.kind = "image";
                oi_p.bytes = (long long)fs::file_size(preview_path);
                oi_p.sha256 = psha;
                R.outputs.push_back(oi_p);
            }
        }

        // Register video if produced
        if (!out_video_path.empty() && fs::exists(out_video_path)) {
            std::string video_sha; sha256_file(out_video_path, video_sha, herr);
            OutputItem oi_v;
            oi_v.output_id = R.run_id + "_delta_visualized_mp4";
            oi_v.path = "outputs/delta_visualized.mp4";
            oi_v.kind = "video";
            oi_v.bytes = (long long)fs::file_size(out_video_path);
            oi_v.sha256 = video_sha;
            R.outputs.push_back(oi_v);
        }

        // Write outputs/delta_tiles.json
        std::ostringstream tj;
        tj << "{\n  \"kernel_id\": \"adaptive_delta_fused\",\n"
           << "  \"input\": " << json_s(R.input) << ",\n"
           << "  \"golden_id\": " << json_s(R.golden_id) << ",\n"
           << "  \"dimensions\": { \"width\": " << width << ", \"height\": " << height << " },\n"
           << "  \"tiles\": { \"tile_dim\": 16, \"tiles_x\": " << tiles_x << ", \"tiles_y\": " << tiles_y << ", \"total_tiles\": " << total_tiles << " },\n"
           << "  \"mse_threshold\": " << mse_threshold << ",\n"
           << "  \"frames_processed\": " << processed_frames << ",\n"
           << "  \"max_mutated_frame\": " << max_mutated_frame << ",\n"
           << "  \"max_mutated_tiles\": " << max_mutated_count << ",\n"
           << "  \"timeline\": [\n";
        for (size_t i = 0; i < timeline.size(); ++i) {
            if (i > 0) tj << ",\n";
            tj << "    { \"frame\": " << timeline[i].frame
               << ", \"mutated_tiles\": " << timeline[i].mutated_tiles
               << ", \"mutated_pct\": " << timeline[i].mutated_pct << " }";
        }
        tj << "\n  ]\n}\n";

        std::string delta_path = R.run_dir + "\\outputs\\delta_tiles.json";
        write_file(delta_path, tj.str());

        std::string delta_sha; sha256_file(delta_path, delta_sha, herr);
        OutputItem oi;
        oi.output_id = R.run_id + "_delta_tiles_json";
        oi.path = "outputs/delta_tiles.json";
        oi.kind = "telemetry_json";
        oi.bytes = (long long)tj.str().size();
        oi.sha256 = delta_sha;
        R.outputs.push_back(oi);

        R.frames = processed_frames;
        R.ok = true;
        return finish("finished");
    }

    if (R.symbol_init.empty()) return fail("resolve", "adapter has no symbol_init (shape " + R.shape + "); main-only shapes not implemented in " + HOST_VERSION);
    std::string init_args = jget(adapter, "init_args");
    if (!init_args.empty() && init_args != "none")
        return fail("resolve", "symbol_init " + R.symbol_init + " takes (" + init_args + "); argument marshalling not implemented in " + HOST_VERSION);

    return fail("resolve", "shape not implemented in " + std::string(HOST_VERSION) + ": '" + R.shape + "'");
}
