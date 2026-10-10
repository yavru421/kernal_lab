
import bpy
import json
import math

timeline = json.loads('''[{"frame": 1, "valid": true, "u": 0.10185416666666663, "v": 0.21968796296296295, "roll": -0.3108540870988515, "scale": 0.9933526394757659, "mouth_open": 0.7641, "eye_blink_l": 0.0372, "eye_blink_r": 0.0453}, {"frame": 2, "valid": true, "u": 0.10188020833333328, "v": 0.2195, "roll": -0.3125306461138408, "scale": 0.9861419047020097, "mouth_open": 0.7716, "eye_blink_l": 0.0441, "eye_blink_r": 0.0822}, {"frame": 3, "valid": true, "u": 0.10188020833333328, "v": 0.21933888888888892, "roll": -0.31029002703906505, "scale": 0.9909608531939348, "mouth_open": 0.7707, "eye_blink_l": 0.0436, "eye_blink_r": 0.0621}, {"frame": 4, "valid": true, "u": 0.10173437499999996, "v": 0.21952777777777777, "roll": -0.30871926195092575, "scale": 0.9993066385588842, "mouth_open": 0.7791, "eye_blink_l": 0.0326, "eye_blink_r": 0.0544}, {"frame": 5, "valid": true, "u": 0.1014583333333333, "v": 0.21987777777777778, "roll": -0.3131980210216805, "scale": 0.9929969441336535, "mouth_open": 0.767, "eye_blink_l": 0.038, "eye_blink_r": 0.0629}, {"frame": 6, "valid": true, "u": 0.10145312499999998, "v": 0.21965462962962962, "roll": -0.3261261575721134, "scale": 0.9894731731502248, "mouth_open": 0.7799, "eye_blink_l": 0.0558, "eye_blink_r": 0.038}, {"frame": 7, "valid": true, "u": 0.10163541666666671, "v": 0.2192222222222222, "roll": -0.3281986291406459, "scale": 0.9968446219951661, "mouth_open": 0.775, "eye_blink_l": 0.0677, "eye_blink_r": 0.0265}, {"frame": 8, "valid": true, "u": 0.10203645833333337, "v": 0.2188212962962963, "roll": -0.3224550867724359, "scale": 0.9926944414323178, "mouth_open": 0.7696, "eye_blink_l": 0.0843, "eye_blink_r": 0.0201}, {"frame": 9, "valid": true, "u": 0.10232291666666668, "v": 0.21892685185185182, "roll": -0.31065219374434033, "scale": 0.993288232885104, "mouth_open": 0.7681, "eye_blink_l": 0.0701, "eye_blink_r": 0.0265}, {"frame": 10, "valid": true, "u": 0.1025572916666667, "v": 0.2191472222222222, "roll": -0.30897472436288687, "scale": 1.0192874127711637, "mouth_open": 0.7792, "eye_blink_l": 0.0455, "eye_blink_r": 0.0342}, {"frame": 11, "valid": true, "u": 0.10269270833333337, "v": 0.2195111111111111, "roll": -0.31393434867691844, "scale": 1.0098433303171732, "mouth_open": 0.7898, "eye_blink_l": 0.0458, "eye_blink_r": 0.0209}, {"frame": 12, "valid": true, "u": 0.10286458333333333, "v": 0.21987962962962965, "roll": -0.31084771544960893, "scale": 0.9988815114699804, "mouth_open": 0.7857, "eye_blink_l": 0.0655, "eye_blink_r": 0.0249}, {"frame": 13, "valid": true, "u": 0.1030885416666667, "v": 0.22034907407407406, "roll": -0.31185120776728714, "scale": 0.9992041423505142, "mouth_open": 0.7923, "eye_blink_l": 0.0508, "eye_blink_r": 0.0178}, {"frame": 14, "valid": true, "u": 0.1031927083333334, "v": 0.2209833333333333, "roll": -0.31183818950022896, "scale": 1.0146914211746023, "mouth_open": 0.7779, "eye_blink_l": 0.0452, "eye_blink_r": 0.0279}, {"frame": 15, "valid": true, "u": 0.10317708333333328, "v": 0.22178425925925924, "roll": -0.317556411808183, "scale": 1.0243420640703769, "mouth_open": 0.7831, "eye_blink_l": 0.0374, "eye_blink_r": 0.07}, {"frame": 16, "valid": true, "u": 0.10310416666666669, "v": 0.22242314814814815, "roll": -0.31919450470065297, "scale": 1.0293320264767098, "mouth_open": 0.7832, "eye_blink_l": 0.0574, "eye_blink_r": 0.0875}, {"frame": 17, "valid": true, "u": 0.10301562499999999, "v": 0.2226962962962963, "roll": -0.32094991405530077, "scale": 1.039919689190971, "mouth_open": 0.7867, "eye_blink_l": 0.0444, "eye_blink_r": 0.0895}, {"frame": 18, "valid": true, "u": 0.10303124999999996, "v": 0.22314537037037038, "roll": -0.3160004870847059, "scale": 1.0193876013352612, "mouth_open": 0.7837, "eye_blink_l": 0.048, "eye_blink_r": 0.0939}, {"frame": 19, "valid": true, "u": 0.10288020833333332, "v": 0.22354907407407407, "roll": -0.2913598116150476, "scale": 1.0401332185027703, "mouth_open": 0.7938, "eye_blink_l": 0.0478, "eye_blink_r": 0.108}, {"frame": 20, "valid": true, "u": 0.10204687500000004, "v": 0.22408333333333333, "roll": -0.21540254576358261, "scale": 1.1470780945764703, "mouth_open": 0.8117, "eye_blink_l": 0.0201, "eye_blink_r": 0.286}, {"frame": 21, "valid": true, "u": 0.10018749999999994, "v": 0.2250111111111111, "roll": -0.24442192992385314, "scale": 1.192886164320848, "mouth_open": 0.8428, "eye_blink_l": 0.0456, "eye_blink_r": 0.383}, {"frame": 22, "valid": true, "u": 0.09723437500000003, "v": 0.22789259259259262, "roll": -0.2761647447446587, "scale": 1.2468005771973265, "mouth_open": 0.8687, "eye_blink_l": 0.1629, "eye_blink_r": 0.4656}, {"frame": 23, "valid": true, "u": 0.09392708333333329, "v": 0.23084629629629633, "roll": -0.28714330875330035, "scale": 1.26284691380528, "mouth_open": 0.8814, "eye_blink_l": 0.2301, "eye_blink_r": 0.5098}, {"frame": 24, "valid": true, "u": 0.09026562499999997, "v": 0.23398425925925923, "roll": -0.29633821754061107, "scale": 1.2399109408298838, "mouth_open": 0.8701, "eye_blink_l": 0.3304, "eye_blink_r": 0.5345}, {"frame": 25, "valid": true, "u": 0.08698437499999999, "v": 0.23630185185185187, "roll": -0.3021452235394394, "scale": 1.189183571519162, "mouth_open": 0.8068, "eye_blink_l": 0.3648, "eye_blink_r": 0.5185}, {"frame": 26, "valid": true, "u": 0.08406250000000005, "v": 0.2383037037037037, "roll": -0.2516781762173702, "scale": 1.2353151650174385, "mouth_open": 0.7958, "eye_blink_l": 0.3598, "eye_blink_r": 0.5273}, {"frame": 27, "valid": true, "u": 0.08187500000000002, "v": 0.24000370370370372, "roll": -0.2867721346846239, "scale": 1.162789915946138, "mouth_open": 0.7077, "eye_blink_l": 0.4134, "eye_blink_r": 0.5617}, {"frame": 28, "valid": true, "u": 0.07950520833333338, "v": 0.24131203703703705, "roll": -0.2745822040106677, "scale": 1.237489950461028, "mouth_open": 0.6984, "eye_blink_l": 0.3683, "eye_blink_r": 0.5842}, {"frame": 29, "valid": true, "u": 0.07777604166666663, "v": 0.2421, "roll": -0.29036725117639495, "scale": 1.2036020228472684, "mouth_open": 0.6403, "eye_blink_l": 0.3738, "eye_blink_r": 0.5997}, {"frame": 30, "valid": true, "u": 0.07659374999999997, "v": 0.2431, "roll": -0.2798450491542154, "scale": 1.2075664084468996, "mouth_open": 0.631, "eye_blink_l": 0.3934, "eye_blink_r": 0.6167}, {"frame": 31, "valid": true, "u": 0.07577604166666667, "v": 0.24306944444444442, "roll": -0.3005552645300926, "scale": 1.1974167894769678, "mouth_open": 0.6231, "eye_blink_l": 0.3987, "eye_blink_r": 0.6088}, {"frame": 32, "valid": true, "u": 0.07536458333333336, "v": 0.24282037037037035, "roll": -0.2810735603394812, "scale": 1.2047052619346692, "mouth_open": 0.649, "eye_blink_l": 0.4021, "eye_blink_r": 0.6166}, {"frame": 33, "valid": true, "u": 0.07515104166666665, "v": 0.24247685185185186, "roll": -0.2873835988291784, "scale": 1.2135173096529543, "mouth_open": 0.6358, "eye_blink_l": 0.3986, "eye_blink_r": 0.6081}, {"frame": 34, "valid": true, "u": 0.07493229166666661, "v": 0.2409611111111111, "roll": -0.29070119055820454, "scale": 1.201523624443799, "mouth_open": 0.6227, "eye_blink_l": 0.3908, "eye_blink_r": 0.6168}, {"frame": 35, "valid": true, "u": 0.07538020833333334, "v": 0.23992962962962966, "roll": -0.283637946829116, "scale": 1.186952849015344, "mouth_open": 0.6022, "eye_blink_l": 0.3969, "eye_blink_r": 0.6228}, {"frame": 36, "valid": true, "u": 0.07634895833333329, "v": 0.23841759259259257, "roll": -0.2903652568502806, "scale": 1.2014029470383498, "mouth_open": 0.6141, "eye_blink_l": 0.3935, "eye_blink_r": 0.6195}, {"frame": 37, "valid": true, "u": 0.07883333333333328, "v": 0.23770462962962963, "roll": -0.27939799470105364, "scale": 1.2380897336575745, "mouth_open": 0.6364, "eye_blink_l": 0.3817, "eye_blink_r": 0.6045}, {"frame": 38, "valid": true, "u": 0.08246354166666663, "v": 0.2360287037037037, "roll": -0.2800597778814739, "scale": 1.2657216958207382, "mouth_open": 0.6539, "eye_blink_l": 0.3959, "eye_blink_r": 0.6148}, {"frame": 39, "valid": true, "u": 0.08929687500000003, "v": 0.23348888888888888, "roll": -0.26327667248350384, "scale": 1.3318076909198293, "mouth_open": 0.7424, "eye_blink_l": 0.3641, "eye_blink_r": 0.5803}, {"frame": 40, "valid": true, "u": 0.09785937500000005, "v": 0.2285074074074074, "roll": -0.24509026196577452, "scale": 1.3732965503659882, "mouth_open": 0.8912, "eye_blink_l": 0.3422, "eye_blink_r": 0.4733}, {"frame": 41, "valid": true, "u": 0.10977083333333333, "v": 0.22249074074074077, "roll": -0.3173346436621303, "scale": 1.2670321127274942, "mouth_open": 0.823, "eye_blink_l": 0.1693, "eye_blink_r": 0.2682}, {"frame": 42, "valid": true, "u": 0.12189583333333331, "v": 0.2164472222222222, "roll": -0.245636413525326, "scale": 1.1650187638837102, "mouth_open": 0.7971, "eye_blink_l": 0.1289, "eye_blink_r": 0.2444}, {"frame": 43, "valid": true, "u": 0.1334895833333333, "v": 0.21099074074074076, "roll": -0.2467240524311733, "scale": 1.17076748142931, "mouth_open": 0.6912, "eye_blink_l": 0.0482, "eye_blink_r": 0.1435}, {"frame": 44, "valid": true, "u": 0.1434270833333334, "v": 0.20699351851851852, "roll": -0.2623105316280381, "scale": 1.1319059221091983, "mouth_open": 0.5833, "eye_blink_l": 0.0, "eye_blink_r": 0.0969}, {"frame": 45, "valid": true, "u": 0.15116145833333333, "v": 0.20474722222222222, "roll": -0.37400195510422085, "scale": 0.9922166428203323, "mouth_open": 0.5041, "eye_blink_l": 0.0, "eye_blink_r": 0.0558}, {"frame": 46, "valid": true, "u": 0.15611458333333333, "v": 0.20393981481481482, "roll": -0.42731307671781577, "scale": 0.9153620495322495, "mouth_open": 0.3952, "eye_blink_l": 0.0904, "eye_blink_r": 0.0997}, {"frame": 47, "valid": true, "u": 0.1591458333333333, "v": 0.2045962962962963, "roll": -0.5492549271353768, "scale": 0.7359331585084418, "mouth_open": 0.2872, "eye_blink_l": 0.385, "eye_blink_r": 0.1667}, {"frame": 48, "valid": true, "u": 0.15984895833333337, "v": 0.20502962962962964, "roll": -0.5693911455751073, "scale": 0.6827464837403134, "mouth_open": 0.201, "eye_blink_l": 0.5775, "eye_blink_r": 0.313}, {"frame": 49, "valid": true, "u": 0.15940104166666663, "v": 0.2036314814814815, "roll": -0.591854519859462, "scale": 0.6218184759190619, "mouth_open": 0.1469, "eye_blink_l": 0.774, "eye_blink_r": 0.3637}, {"frame": 50, "valid": true, "u": 0.15591666666666662, "v": 0.20199259259259258, "roll": -0.5786641571957527, "scale": 0.5786673127750603, "mouth_open": 0.095, "eye_blink_l": 0.8752, "eye_blink_r": 0.5659}, {"frame": 51, "valid": true, "u": 0.15050000000000002, "v": 0.19943333333333332, "roll": -0.6155903307403553, "scale": 0.4966352584952357, "mouth_open": 0.0454, "eye_blink_l": 0.9781, "eye_blink_r": 0.7283}, {"frame": 52, "valid": true, "u": 0.14390624999999999, "v": 0.19678055555555557, "roll": -0.5050198139936058, "scale": 0.5511538017080195, "mouth_open": 0.0563, "eye_blink_l": 0.8832, "eye_blink_r": 0.7742}, {"frame": 53, "valid": true, "u": 0.13685416666666667, "v": 0.19471574074074074, "roll": -0.5763752205911858, "scale": 0.4748048560892675, "mouth_open": 0.0247, "eye_blink_l": 0.9262, "eye_blink_r": 0.8998}, {"frame": 54, "valid": true, "u": 0.13034895833333332, "v": 0.1936314814814815, "roll": -0.5762683761357176, "scale": 0.41322738262125297, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 55, "valid": true, "u": 0.1246458333333333, "v": 0.19339722222222225, "roll": -0.6107259643892055, "scale": 0.3136751939869696, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 56, "valid": true, "u": 0.11888020833333333, "v": 0.19438611111111112, "roll": -0.6020232250982027, "scale": 0.28750909457530965, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 57, "valid": true, "u": 0.11272395833333336, "v": 0.19571481481481484, "roll": -0.6155495434049664, "scale": 0.2683042960010359, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 58, "valid": true, "u": 0.10580208333333338, "v": 0.19689722222222222, "roll": -0.6255477174982832, "scale": 0.30270789687038224, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 59, "valid": true, "u": 0.09871874999999998, "v": 0.19776851851851848, "roll": -0.6703251243448962, "scale": 0.26073154869094345, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 60, "valid": true, "u": 0.09122916666666671, "v": 0.19979537037037037, "roll": -0.690790928277697, "scale": 0.2664542311218556, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 61, "valid": true, "u": 0.08305208333333335, "v": 0.20150648148148148, "roll": -0.5563759013994157, "scale": 0.31129628201359805, "mouth_open": 0.0, "eye_blink_l": 1.0, "eye_blink_r": 1.0}, {"frame": 62, "valid": true, "u": 0.0732760416666667, "v": 0.2043888888888889, "roll": -0.5595340158372824, "scale": 0.4299642066895932, "mouth_open": 0.0046, "eye_blink_l": 0.9912, "eye_blink_r": 0.9496}, {"frame": 63, "valid": true, "u": 0.0607760416666667, "v": 0.20782314814814815, "roll": -0.49395363900879574, "scale": 0.5813280085231737, "mouth_open": 0.0758, "eye_blink_l": 0.8365, "eye_blink_r": 0.6863}, {"frame": 64, "valid": true, "u": 0.04563541666666661, "v": 0.2103675925925926, "roll": -0.5374295662610508, "scale": 0.6644915846321947, "mouth_open": 0.1762, "eye_blink_l": 0.4532, "eye_blink_r": 0.5644}, {"frame": 65, "valid": true, "u": 0.031625000000000014, "v": 0.21271111111111113, "roll": -0.37546754846490193, "scale": 0.815060334614209, "mouth_open": 0.3273, "eye_blink_l": 0.0539, "eye_blink_r": 0.227}, {"frame": 66, "valid": true, "u": 0.018165104166666644, "v": 0.21408796296296295, "roll": -0.2309949779947178, "scale": 1.008333855719052, "mouth_open": 0.4604, "eye_blink_l": 0.0, "eye_blink_r": 0.2495}, {"frame": 67, "valid": true, "u": 0.005947916666666646, "v": 0.21500185185185186, "roll": -0.20488837624619682, "scale": 1.033714912187076, "mouth_open": 0.4832, "eye_blink_l": 0.0, "eye_blink_r": 0.1835}, {"frame": 68, "valid": true, "u": -0.005410937500000005, "v": 0.21448425925925924, "roll": -0.21972751993160963, "scale": 1.100694403058762, "mouth_open": 0.6338, "eye_blink_l": 0.0, "eye_blink_r": 0.0559}, {"frame": 69, "valid": true, "u": -0.015422395833333328, "v": 0.21395925925925927, "roll": -0.19739555984988286, "scale": 1.1223548168948534, "mouth_open": 0.68, "eye_blink_l": 0.0, "eye_blink_r": 0.0001}, {"frame": 70, "valid": true, "u": -0.02419531250000002, "v": 0.21380185185185185, "roll": -0.17034769158951002, "scale": 1.0989836909945727, "mouth_open": 0.6902, "eye_blink_l": 0.0, "eye_blink_r": 0.0424}, {"frame": 71, "valid": true, "u": -0.03132395833333336, "v": 0.2144666666666667, "roll": -0.25401228850491614, "scale": 1.082967337298517, "mouth_open": 0.6826, "eye_blink_l": 0.0329, "eye_blink_r": 0.0275}, {"frame": 72, "valid": true, "u": -0.03701927083333333, "v": 0.21437222222222221, "roll": -0.2714205347874828, "scale": 1.0830207626724535, "mouth_open": 0.7083, "eye_blink_l": 0.0585, "eye_blink_r": 0.047}, {"frame": 73, "valid": true, "u": -0.04159427083333333, "v": 0.21438703703703704, "roll": -0.32633767818603704, "scale": 1.089054306034817, "mouth_open": 0.7243, "eye_blink_l": 0.0411, "eye_blink_r": 0.1216}, {"frame": 74, "valid": true, "u": -0.04463177083333333, "v": 0.21374814814814816, "roll": -0.2980414956591191, "scale": 1.0325496160023682, "mouth_open": 0.784, "eye_blink_l": 0.078, "eye_blink_r": 0.0817}, {"frame": 75, "valid": true, "u": -0.046489062500000004, "v": 0.21346018518518517, "roll": -0.32085624838485266, "scale": 1.0054833571999962, "mouth_open": 0.8065, "eye_blink_l": 0.0745, "eye_blink_r": 0.0541}, {"frame": 76, "valid": true, "u": -0.04721354166666666, "v": 0.21313888888888888, "roll": -0.3395334537449609, "scale": 0.9945166428000038, "mouth_open": 0.8057, "eye_blink_l": 0.08, "eye_blink_r": 0.0646}, {"frame": 77, "valid": true, "u": -0.046534375, "v": 0.21236111111111114, "roll": -0.3656302357863016, "scale": 1.0188861082285734, "mouth_open": 0.8079, "eye_blink_l": 0.0984, "eye_blink_r": 0.0502}, {"frame": 78, "valid": true, "u": -0.04464375, "v": 0.2114898148148148, "roll": -0.37976489428231724, "scale": 0.9758855350343937, "mouth_open": 0.8107, "eye_blink_l": 0.1466, "eye_blink_r": 0.0267}, {"frame": 79, "valid": true, "u": -0.04126406249999999, "v": 0.21031759259259256, "roll": -0.40822346721699426, "scale": 0.9837142534884925, "mouth_open": 0.7918, "eye_blink_l": 0.1469, "eye_blink_r": 0.0}, {"frame": 80, "valid": true, "u": -0.03614427083333336, "v": 0.20954444444444445, "roll": -0.40911979491579814, "scale": 0.9877694490087721, "mouth_open": 0.7586, "eye_blink_l": 0.1223, "eye_blink_r": 0.0156}, {"frame": 81, "valid": true, "u": -0.030051041666666656, "v": 0.20868425925925926, "roll": -0.40864369364152303, "scale": 0.9877952303232151, "mouth_open": 0.7237, "eye_blink_l": 0.116, "eye_blink_r": 0.0}, {"frame": 82, "valid": true, "u": -0.02229739583333335, "v": 0.20742962962962963, "roll": -0.37119981684862646, "scale": 0.989774357488692, "mouth_open": 0.7299, "eye_blink_l": 0.1463, "eye_blink_r": 0.0217}, {"frame": 83, "valid": true, "u": -0.01344583333333335, "v": 0.20658055555555557, "roll": -0.3747302109358747, "scale": 0.988652805443138, "mouth_open": 0.7309, "eye_blink_l": 0.1299, "eye_blink_r": 0.0021}, {"frame": 84, "valid": true, "u": -0.004208333333333355, "v": 0.20574629629629632, "roll": -0.3654297562768873, "scale": 0.9884748575315491, "mouth_open": 0.7293, "eye_blink_l": 0.146, "eye_blink_r": 0.0}, {"frame": 85, "valid": true, "u": 0.005480208333333359, "v": 0.20476759259259258, "roll": -0.35137801291872706, "scale": 0.9870993591818777, "mouth_open": 0.7394, "eye_blink_l": 0.1569, "eye_blink_r": 0.0}, {"frame": 86, "valid": true, "u": 0.015266145833333352, "v": 0.20413425925925924, "roll": -0.3425343443765908, "scale": 0.9839479105480339, "mouth_open": 0.7219, "eye_blink_l": 0.1541, "eye_blink_r": 0.0}, {"frame": 87, "valid": true, "u": 0.025432291666666686, "v": 0.20420555555555553, "roll": -0.32550842155523113, "scale": 0.9926012914084421, "mouth_open": 0.6999, "eye_blink_l": 0.1445, "eye_blink_r": 0.0}, {"frame": 88, "valid": true, "u": 0.03619791666666667, "v": 0.20478611111111109, "roll": -0.3231105562118165, "scale": 1.004018504878202, "mouth_open": 0.7141, "eye_blink_l": 0.1275, "eye_blink_r": 0.0}, {"frame": 89, "valid": true, "u": 0.04638541666666664, "v": 0.20526388888888888, "roll": -0.3277985309101848, "scale": 0.9967089113427523, "mouth_open": 0.7603, "eye_blink_l": 0.1395, "eye_blink_r": 0.0}, {"frame": 90, "valid": true, "u": 0.05615624999999997, "v": 0.20630092592592594, "roll": -0.3295675140080288, "scale": 1.0140064712911712, "mouth_open": 0.7739, "eye_blink_l": 0.1054, "eye_blink_r": 0.0351}, {"frame": 91, "valid": true, "u": 0.06591145833333331, "v": 0.20795092592592593, "roll": -0.3213583462849673, "scale": 1.0189711788569424, "mouth_open": 0.7664, "eye_blink_l": 0.1201, "eye_blink_r": 0.0765}, {"frame": 92, "valid": true, "u": 0.07520312500000005, "v": 0.2096166666666667, "roll": -0.31416056732041564, "scale": 1.0531047940601492, "mouth_open": 0.7511, "eye_blink_l": 0.1039, "eye_blink_r": 0.1019}, {"frame": 93, "valid": true, "u": 0.08475000000000002, "v": 0.21131296296296298, "roll": -0.3206108815964059, "scale": 1.0520094138247704, "mouth_open": 0.7611, "eye_blink_l": 0.0898, "eye_blink_r": 0.1162}, {"frame": 94, "valid": true, "u": 0.09393229166666663, "v": 0.21281851851851852, "roll": -0.24166192570370595, "scale": 1.155190791582972, "mouth_open": 0.8066, "eye_blink_l": 0.0057, "eye_blink_r": 0.3495}, {"frame": 95, "valid": true, "u": 0.10234895833333332, "v": 0.21432037037037038, "roll": -0.2491582320330515, "scale": 1.1856165658256894, "mouth_open": 0.8009, "eye_blink_l": 0.0, "eye_blink_r": 0.3577}, {"frame": 96, "valid": true, "u": 0.1103697916666667, "v": 0.21509351851851852, "roll": -0.22510200917142575, "scale": 1.1258024270852784, "mouth_open": 0.7717, "eye_blink_l": 0.065, "eye_blink_r": 0.2586}, {"frame": 97, "valid": true, "u": 0.11801041666666663, "v": 0.21590185185185184, "roll": -0.24716624508984567, "scale": 1.1209338896394367, "mouth_open": 0.7607, "eye_blink_l": 0.1062, "eye_blink_r": 0.1564}, {"frame": 98, "valid": true, "u": 0.12502604166666664, "v": 0.2164407407407407, "roll": -0.23290254319597145, "scale": 1.1549110457662823, "mouth_open": 0.8163, "eye_blink_l": 0.1151, "eye_blink_r": 0.2153}, {"frame": 99, "valid": true, "u": 0.131921875, "v": 0.2179472222222222, "roll": -0.23319103762456692, "scale": 1.1398356234784655, "mouth_open": 0.8101, "eye_blink_l": 0.1262, "eye_blink_r": 0.1908}, {"frame": 100, "valid": true, "u": 0.13805729166666664, "v": 0.2184787037037037, "roll": -0.2106603135277294, "scale": 1.1211315736849463, "mouth_open": 0.7967, "eye_blink_l": 0.1275, "eye_blink_r": 0.1698}, {"frame": 101, "valid": true, "u": 0.14278125000000005, "v": 0.2185564814814815, "roll": -0.20396382256270193, "scale": 1.1163271864087096, "mouth_open": 0.8237, "eye_blink_l": 0.1238, "eye_blink_r": 0.2542}, {"frame": 102, "valid": true, "u": 0.14637499999999998, "v": 0.2161509259259259, "roll": -0.21470754737422731, "scale": 1.1275014585247698, "mouth_open": 0.9209, "eye_blink_l": 0.1485, "eye_blink_r": 0.3642}, {"frame": 103, "valid": true, "u": 0.14880208333333336, "v": 0.21159259259259258, "roll": -0.22985871280129813, "scale": 1.1454302048111504, "mouth_open": 0.9428, "eye_blink_l": 0.1606, "eye_blink_r": 0.4475}, {"frame": 104, "valid": true, "u": 0.15084374999999994, "v": 0.20497870370370372, "roll": -0.22638850749423475, "scale": 1.1542344427960618, "mouth_open": 0.9767, "eye_blink_l": 0.1231, "eye_blink_r": 0.541}, {"frame": 105, "valid": true, "u": 0.1527708333333333, "v": 0.19840185185185186, "roll": -0.30428431649720245, "scale": 1.1403052120920836, "mouth_open": 0.9998, "eye_blink_l": 0.2271, "eye_blink_r": 0.4701}, {"frame": 106, "valid": true, "u": 0.15430208333333334, "v": 0.19329074074074076, "roll": -0.27107395241047516, "scale": 1.1532015561172357, "mouth_open": 0.9785, "eye_blink_l": 0.1687, "eye_blink_r": 0.534}, {"frame": 107, "valid": true, "u": 0.15582812500000004, "v": 0.1907675925925926, "roll": -0.2265959671477602, "scale": 1.1283505333946868, "mouth_open": 0.9665, "eye_blink_l": 0.1441, "eye_blink_r": 0.4967}, {"frame": 108, "valid": true, "u": 0.1573697916666667, "v": 0.1908027777777778, "roll": -0.20318655371968897, "scale": 1.159159566778804, "mouth_open": 0.9554, "eye_blink_l": 0.147, "eye_blink_r": 0.4864}, {"frame": 109, "valid": true, "u": 0.1586302083333333, "v": 0.19205092592592596, "roll": -0.21825828434081554, "scale": 1.1682963779894948, "mouth_open": 0.9703, "eye_blink_l": 0.1423, "eye_blink_r": 0.4868}, {"frame": 110, "valid": true, "u": 0.1597083333333334, "v": 0.19415185185185188, "roll": -0.21927913597414672, "scale": 1.1232433907685802, "mouth_open": 0.9466, "eye_blink_l": 0.2011, "eye_blink_r": 0.4025}, {"frame": 111, "valid": true, "u": 0.16086979166666662, "v": 0.19532500000000003, "roll": -0.25518239062082465, "scale": 1.1265071495553363, "mouth_open": 0.9404, "eye_blink_l": 0.1776, "eye_blink_r": 0.4288}, {"frame": 112, "valid": true, "u": 0.16183333333333336, "v": 0.1960361111111111, "roll": -0.2884595282489547, "scale": 1.1106398077387125, "mouth_open": 0.9671, "eye_blink_l": 0.2018, "eye_blink_r": 0.4492}, {"frame": 113, "valid": true, "u": 0.16243229166666662, "v": 0.1950962962962963, "roll": -0.29543280636979513, "scale": 1.0909526232596984, "mouth_open": 1.0, "eye_blink_l": 0.2315, "eye_blink_r": 0.4584}, {"frame": 114, "valid": true, "u": 0.16252604166666665, "v": 0.19400740740740743, "roll": -0.28180071592370853, "scale": 1.10737774125107, "mouth_open": 1.0, "eye_blink_l": 0.1939, "eye_blink_r": 0.4767}, {"frame": 115, "valid": true, "u": 0.16220833333333337, "v": 0.19302037037037037, "roll": -0.2749262217653639, "scale": 1.1106756044211985, "mouth_open": 1.0, "eye_blink_l": 0.199, "eye_blink_r": 0.4931}, {"frame": 116, "valid": true, "u": 0.16176562499999997, "v": 0.1916990740740741, "roll": -0.26943791432227293, "scale": 1.1133458777572842, "mouth_open": 1.0, "eye_blink_l": 0.2048, "eye_blink_r": 0.4755}, {"frame": 117, "valid": true, "u": 0.16095312499999997, "v": 0.1901287037037037, "roll": -0.2564894117110318, "scale": 1.1051166420944414, "mouth_open": 1.0, "eye_blink_l": 0.2288, "eye_blink_r": 0.4502}, {"frame": 118, "valid": true, "u": 0.15989583333333332, "v": 0.18924166666666664, "roll": -0.24744900231853875, "scale": 1.0960300780399168, "mouth_open": 1.0, "eye_blink_l": 0.2288, "eye_blink_r": 0.4386}, {"frame": 119, "valid": true, "u": 0.15888541666666664, "v": 0.18846944444444447, "roll": -0.2520735381664638, "scale": 1.1016739322477391, "mouth_open": 0.9881, "eye_blink_l": 0.212, "eye_blink_r": 0.4243}, {"frame": 120, "valid": true, "u": 0.1577395833333333, "v": 0.1874009259259259, "roll": -0.268155966885772, "scale": 1.0867399684248658, "mouth_open": 1.0, "eye_blink_l": 0.2103, "eye_blink_r": 0.3945}, {"frame": 121, "valid": true, "u": 0.15670312499999994, "v": 0.1865851851851852, "roll": -0.2587653947851238, "scale": 1.0894379898923292, "mouth_open": 0.9835, "eye_blink_l": 0.2029, "eye_blink_r": 0.3813}, {"frame": 122, "valid": true, "u": 0.15566145833333328, "v": 0.18630925925925926, "roll": -0.2298014471352903, "scale": 1.0805188323451485, "mouth_open": 0.9498, "eye_blink_l": 0.1745, "eye_blink_r": 0.3696}, {"frame": 123, "valid": true, "u": 0.1547552083333334, "v": 0.1867083333333333, "roll": -0.23095318022938802, "scale": 1.0526815426282103, "mouth_open": 0.9355, "eye_blink_l": 0.1642, "eye_blink_r": 0.349}, {"frame": 124, "valid": true, "u": 0.15427083333333336, "v": 0.1879861111111111, "roll": -0.2342285655948594, "scale": 1.1357862611937384, "mouth_open": 0.8966, "eye_blink_l": 0.0951, "eye_blink_r": 0.4115}, {"frame": 125, "valid": true, "u": 0.15412500000000004, "v": 0.19001388888888887, "roll": -0.20385727347597196, "scale": 1.1507165436835234, "mouth_open": 0.9291, "eye_blink_l": 0.077, "eye_blink_r": 0.3787}, {"frame": 126, "valid": true, "u": 0.15395833333333328, "v": 0.19172685185185184, "roll": -0.21488705097601432, "scale": 1.174975830505985, "mouth_open": 0.9182, "eye_blink_l": 0.0643, "eye_blink_r": 0.3347}, {"frame": 127, "valid": true, "u": 0.15343229166666664, "v": 0.19347499999999998, "roll": -0.2455300576397438, "scale": 1.1117869646184557, "mouth_open": 0.8885, "eye_blink_l": 0.1049, "eye_blink_r": 0.1863}, {"frame": 128, "valid": true, "u": 0.15220312500000002, "v": 0.19572592592592594, "roll": -0.26688675545373536, "scale": 1.1496876018888156, "mouth_open": 0.8096, "eye_blink_l": 0.1032, "eye_blink_r": 0.135}, {"frame": 129, "valid": true, "u": 0.1505677083333333, "v": 0.19692777777777778, "roll": -0.287996232239097, "scale": 1.1368489763475444, "mouth_open": 0.8841, "eye_blink_l": 0.0606, "eye_blink_r": 0.1002}, {"frame": 130, "valid": true, "u": 0.14885937499999996, "v": 0.19733796296296297, "roll": -0.3177117803304748, "scale": 1.1297163225389095, "mouth_open": 0.8821, "eye_blink_l": 0.0325, "eye_blink_r": 0.0988}, {"frame": 131, "valid": true, "u": 0.1469635416666667, "v": 0.1967509259259259, "roll": -0.30401994792165227, "scale": 1.1402105899929127, "mouth_open": 0.8222, "eye_blink_l": 0.0308, "eye_blink_r": 0.1231}, {"frame": 132, "valid": true, "u": 0.14502083333333335, "v": 0.1958722222222222, "roll": -0.2964130868911761, "scale": 1.1804750602315448, "mouth_open": 0.8092, "eye_blink_l": 0.0498, "eye_blink_r": 0.204}, {"frame": 133, "valid": true, "u": 0.1430364583333334, "v": 0.19528425925925924, "roll": -0.295143018672887, "scale": 1.1767160023080832, "mouth_open": 0.8402, "eye_blink_l": 0.035, "eye_blink_r": 0.2723}, {"frame": 134, "valid": true, "u": 0.14135937500000004, "v": 0.19525370370370373, "roll": -0.27121525523995244, "scale": 1.1762024804044233, "mouth_open": 0.8393, "eye_blink_l": 0.0442, "eye_blink_r": 0.2267}, {"frame": 135, "valid": true, "u": 0.13984895833333333, "v": 0.19539166666666669, "roll": -0.27999306422433123, "scale": 1.170359165645744, "mouth_open": 0.8504, "eye_blink_l": 0.0358, "eye_blink_r": 0.2181}, {"frame": 136, "valid": true, "u": 0.13847395833333329, "v": 0.1955583333333333, "roll": -0.29523480419662557, "scale": 1.148128198859076, "mouth_open": 0.8488, "eye_blink_l": 0.04, "eye_blink_r": 0.1793}, {"frame": 137, "valid": true, "u": 0.13742187499999994, "v": 0.19573240740740744, "roll": -0.30226595914592636, "scale": 1.1572361051971836, "mouth_open": 0.8417, "eye_blink_l": 0.0327, "eye_blink_r": 0.1685}, {"frame": 138, "valid": true, "u": 0.13664062499999996, "v": 0.19620833333333332, "roll": -0.2997839356061202, "scale": 1.162958702079064, "mouth_open": 0.8452, "eye_blink_l": 0.0468, "eye_blink_r": 0.2337}, {"frame": 139, "valid": true, "u": 0.13605208333333335, "v": 0.19627407407407407, "roll": -0.30666214937553776, "scale": 1.1809299635316086, "mouth_open": 0.8271, "eye_blink_l": 0.0459, "eye_blink_r": 0.222}, {"frame": 140, "valid": true, "u": 0.13564583333333335, "v": 0.19554907407407407, "roll": -0.31347871054869547, "scale": 1.1635838443522453, "mouth_open": 0.7992, "eye_blink_l": 0.0266, "eye_blink_r": 0.2015}, {"frame": 141, "valid": true, "u": 0.13496354166666671, "v": 0.19467314814814815, "roll": -0.32122104923932193, "scale": 1.1321384640415082, "mouth_open": 0.8714, "eye_blink_l": 0.0476, "eye_blink_r": 0.182}, {"frame": 142, "valid": true, "u": 0.13419791666666672, "v": 0.19315555555555555, "roll": -0.3009876111373851, "scale": 1.132515626447614, "mouth_open": 0.8657, "eye_blink_l": 0.0609, "eye_blink_r": 0.1518}, {"frame": 143, "valid": true, "u": 0.13321875, "v": 0.1914398148148148, "roll": -0.28826884866924063, "scale": 1.1391378224190223, "mouth_open": 0.9029, "eye_blink_l": 0.0754, "eye_blink_r": 0.1701}, {"frame": 144, "valid": true, "u": 0.13234374999999995, "v": 0.18953611111111113, "roll": -0.2974080477208213, "scale": 1.135671954269513, "mouth_open": 0.8491, "eye_blink_l": 0.0933, "eye_blink_r": 0.1229}, {"frame": 145, "valid": true, "u": 0.13182812499999993, "v": 0.18763981481481481, "roll": -0.2911055876578184, "scale": 1.1488968141503797, "mouth_open": 0.8583, "eye_blink_l": 0.1149, "eye_blink_r": 0.1625}, {"frame": 146, "valid": true, "u": 0.13102604166666662, "v": 0.18687407407407408, "roll": -0.2642651043609184, "scale": 1.1761441307453426, "mouth_open": 0.8232, "eye_blink_l": 0.1203, "eye_blink_r": 0.17}, {"frame": 147, "valid": true, "u": 0.1306822916666667, "v": 0.18738888888888888, "roll": -0.30180045060115257, "scale": 1.1703045194358295, "mouth_open": 0.9362, "eye_blink_l": 0.1125, "eye_blink_r": 0.2313}, {"frame": 148, "valid": true, "u": 0.1301875, "v": 0.18790462962962964, "roll": -0.3411136765845961, "scale": 1.1644950213056975, "mouth_open": 0.9472, "eye_blink_l": 0.1196, "eye_blink_r": 0.1716}, {"frame": 149, "valid": true, "u": 0.12887500000000002, "v": 0.18804166666666663, "roll": -0.37833471903820676, "scale": 1.1707130579746452, "mouth_open": 0.9805, "eye_blink_l": 0.1536, "eye_blink_r": 0.1216}, {"frame": 150, "valid": true, "u": 0.128390625, "v": 0.1880564814814815, "roll": -0.3818305756391911, "scale": 1.1076600841485662, "mouth_open": 1.0, "eye_blink_l": 0.1834, "eye_blink_r": 0.0459}]''')
Z_DEPTH = -2.0

scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 150

cam_obj = scene.camera
if not cam_obj:
    for obj in scene.objects:
        if obj.type == 'CAMERA':
            cam_obj = obj
            scene.camera = obj
            break
if not cam_obj:
    raise RuntimeError("Camera not found in active scene")

cam = cam_obj.data
sw = cam.sensor_width
f_mm = cam.lens
aspect = scene.render.resolution_x / scene.render.resolution_y
fov_x = 2.0 * math.atan((sw / 2.0) / f_mm)
fov_y = 2.0 * math.atan(((sw / aspect) / 2.0) / f_mm)
span_x = 2.0 * abs(Z_DEPTH) * math.tan(fov_x / 2.0)
span_y = 2.0 * abs(Z_DEPTH) * math.tan(fov_y / 2.0)

# Purge previous character puppet objects
for name in ["Face_Puppet_Root", "Puppet_Head_Card", "Puppet_Mouth", "Puppet_Eyes", "Puppet_Brows"]:
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

# 1. Create Root Empty parented to camera
root_obj = bpy.data.objects.new("Face_Puppet_Root", None)
root_obj.empty_display_type = 'ARROWS'
root_obj.empty_display_size = 0.2
root_obj.parent = cam_obj
scene.collection.objects.link(root_obj)

# Helper material creator
def get_or_create_mat(name, color):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Roughness'].default_value = 0.4
    return mat

mat_skin = get_or_create_mat("Mat_Puppet_Skin", (0.95, 0.76, 0.65, 1.0))
mat_mouth_dark = get_or_create_mat("Mat_Puppet_MouthDark", (0.15, 0.04, 0.05, 1.0))
mat_teeth = get_or_create_mat("Mat_Puppet_Teeth", (0.98, 0.98, 0.98, 1.0))
mat_eyes = get_or_create_mat("Mat_Puppet_Eyes", (0.08, 0.45, 0.85, 1.0))
mat_brows = get_or_create_mat("Mat_Puppet_Brows", (0.20, 0.12, 0.08, 1.0))

# 2. Head Silhouette Mesh (Stylized oval card)
head_mesh = bpy.data.meshes.new("Puppet_Head_Mesh")
head_obj = bpy.data.objects.new("Puppet_Head_Card", head_mesh)
head_obj.parent = root_obj
scene.collection.objects.link(head_obj)

# 8-gon rounded face card
r = 0.42
verts_head = []
for i in range(12):
    ang = 2.0 * math.pi * i / 12.0
    vx = r * math.cos(ang) * 0.85
    vy = r * math.sin(ang) * 1.15
    verts_head.append((vx, vy, 0.0))
faces_head = [list(range(12))]
head_mesh.from_pydata(verts_head, [], faces_head)
head_mesh.update()
head_obj.data.materials.append(mat_skin)

# 3. Dynamic Mouth Mesh with Shape Keys
mouth_mesh = bpy.data.meshes.new("Puppet_Mouth_Mesh")
mouth_obj = bpy.data.objects.new("Puppet_Mouth", mouth_mesh)
mouth_obj.parent = root_obj
mouth_obj.location = (0.0, -0.22, 0.01)
scene.collection.objects.link(mouth_obj)

# Closed mouth resting line / slit
verts_mouth_rest = [
    (-0.16,  0.01, 0.0), # 0: left corner
    (-0.08,  0.03, 0.0), # 1: upper left
    ( 0.00,  0.04, 0.0), # 2: upper mid
    ( 0.08,  0.03, 0.0), # 3: upper right
    ( 0.16,  0.01, 0.0), # 4: right corner
    ( 0.08, -0.01, 0.0), # 5: lower right
    ( 0.00, -0.01, 0.0), # 6: lower mid
    (-0.08, -0.01, 0.0), # 7: lower left
]
faces_mouth = [[0, 1, 2, 3, 4, 5, 6, 7]]
mouth_mesh.from_pydata(verts_mouth_rest, [], faces_mouth)
mouth_mesh.update()
mouth_obj.data.materials.append(mat_mouth_dark)

# Shape keys for mouth
sk_mouth_basis = mouth_obj.shape_key_add(name="Basis")
sk_mouth_open = mouth_obj.shape_key_add(name="Mouth_Open")

# In Mouth_Open: drop lower vertices down and spread aperture
sk_mouth_open.data[5].co = ( 0.10, -0.14, 0.0)
sk_mouth_open.data[6].co = ( 0.00, -0.16, 0.0)
sk_mouth_open.data[7].co = (-0.10, -0.14, 0.0)
sk_mouth_open.data[2].co = ( 0.00,  0.07, 0.0)

# 4. Dynamic Eyes Mesh with Left/Right Blink Shape Keys
eyes_mesh = bpy.data.meshes.new("Puppet_Eyes_Mesh")
eyes_obj = bpy.data.objects.new("Puppet_Eyes", eyes_mesh)
eyes_obj.parent = root_obj
eyes_obj.location = (0.0, 0.10, 0.01)
scene.collection.objects.link(eyes_obj)

# Left eye quad and Right eye quad
verts_eyes_rest = [
    # Left eye (x: -0.20 to -0.08, y: -0.06 to 0.06)
    (-0.20, -0.06, 0.0), (-0.08, -0.06, 0.0), (-0.08, 0.06, 0.0), (-0.20, 0.06, 0.0),
    # Right eye (x: 0.08 to 0.20, y: -0.06 to 0.06)
    ( 0.08, -0.06, 0.0), ( 0.20, -0.06, 0.0), ( 0.20, 0.06, 0.0), ( 0.08, 0.06, 0.0),
]
faces_eyes = [[0, 1, 2, 3], [4, 5, 6, 7]]
eyes_mesh.from_pydata(verts_eyes_rest, [], faces_eyes)
eyes_mesh.update()
eyes_obj.data.materials.append(mat_eyes)

sk_eyes_basis = eyes_obj.shape_key_add(name="Basis")
sk_blink_l = eyes_obj.shape_key_add(name="Eye_Blink_L")
sk_blink_r = eyes_obj.shape_key_add(name="Eye_Blink_R")

# In Eye_Blink_L: flatten top vertices of left eye down to bottom line
sk_blink_l.data[2].co = (-0.08, -0.05, 0.0)
sk_blink_l.data[3].co = (-0.20, -0.05, 0.0)

# In Eye_Blink_R: flatten top vertices of right eye down to bottom line
sk_blink_r.data[6].co = ( 0.20, -0.05, 0.0)
sk_blink_r.data[7].co = ( 0.08, -0.05, 0.0)

# 5. Eyebrows
brows_mesh = bpy.data.meshes.new("Puppet_Brows_Mesh")
brows_obj = bpy.data.objects.new("Puppet_Brows", brows_mesh)
brows_obj.parent = root_obj
brows_obj.location = (0.0, 0.22, 0.01)
scene.collection.objects.link(brows_obj)

verts_brows = [
    (-0.22, 0.0, 0.0), (-0.08, 0.04, 0.0), (-0.08, 0.06, 0.0), (-0.22, 0.02, 0.0),
    ( 0.08, 0.04, 0.0), ( 0.22, 0.0, 0.0), ( 0.22, 0.02, 0.0), ( 0.08, 0.06, 0.0),
]
faces_brows = [[0, 1, 2, 3], [4, 5, 6, 7]]
brows_mesh.from_pydata(verts_brows, [], faces_brows)
brows_mesh.update()
brows_obj.data.materials.append(mat_brows)

# 6. Apply Animation Keyframes
for item in timeline:
    f_idx = item["frame"]
    scene.frame_set(f_idx)

    if not item.get("valid", False):
        continue

    # Camera-space position
    x_cam = item["u"] * span_x
    y_cam = item["v"] * span_y
    root_obj.location = (x_cam, y_cam, Z_DEPTH)
    root_obj.keyframe_insert(data_path="location", frame=f_idx)

    # 2D Roll rotation around Z
    root_obj.rotation_euler = (0.0, 0.0, item["roll"])
    root_obj.keyframe_insert(data_path="rotation_euler", frame=f_idx)

    # Scale
    s = item["scale"]
    root_obj.scale = (s, s, s)
    root_obj.keyframe_insert(data_path="scale", frame=f_idx)

    # Shape Key: Mouth Open
    sk_mouth_open.value = item["mouth_open"]
    sk_mouth_open.keyframe_insert(data_path="value", frame=f_idx)

    # Shape Key: Left Blink
    sk_blink_l.value = item["eye_blink_l"]
    sk_blink_l.keyframe_insert(data_path="value", frame=f_idx)

    # Shape Key: Right Blink
    sk_blink_r.value = item["eye_blink_r"]
    sk_blink_r.keyframe_insert(data_path="value", frame=f_idx)

scene.frame_set(1)

RESULT = {
    "status": "ok",
    "total_keyframes": len(timeline),
    "rig_objects": ["Face_Puppet_Root", "Puppet_Head_Card", "Puppet_Mouth", "Puppet_Eyes", "Puppet_Brows"],
    "shape_keys": ["Mouth_Open", "Eye_Blink_L", "Eye_Blink_R"]
}
