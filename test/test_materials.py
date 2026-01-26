import unittest
from io import StringIO
import pandas as pd
import numpy as np

from steer_opencell_design.Materials.ActiveMaterials import CathodeMaterial, AnodeMaterial
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive
from steer_opencell_design.Materials.Electrolytes import Electrolyte


class TestLFPSingleCurve(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        half_cell_data = StringIO(
            """
            Specific Capacity (mAh/g),Voltage (V),Step Name,Step_ID
            0.227014756,2.743703704,CC_Chg,1
            0.227014756,3.354074074,CC_Chg,1
            0.227014756,3.460740741,CC_Chg,1
            0.454029512,3.49037037,CC_Chg,1
            0.908059024,3.508148148,CC_Chg,1
            1.816118048,3.502222222,CC_Chg,1
            3.405221339,3.496296296,CC_Chg,1
            4.994324631,3.49037037,CC_Chg,1
            7.264472191,3.49037037,CC_Chg,1
            11.12372304,3.484444444,CC_Chg,1
            21.79341657,3.478518519,CC_Chg,1
            33.82519864,3.472592593,CC_Chg,1
            46.08399546,3.472592593,CC_Chg,1
            57.43473326,3.472592593,CC_Chg,1
            67.19636776,3.472592593,CC_Chg,1
            76.73098751,3.472592593,CC_Chg,1
            81.72531215,3.472592593,CC_Chg,1
            87.17366629,3.472592593,CC_Chg,1
            93.98410897,3.478518519,CC_Chg,1
            98.29738933,3.478518519,CC_Chg,1
            102.1566402,3.484444444,CC_Chg,1
            107.3779796,3.484444444,CC_Chg,1
            112.1452894,3.484444444,CC_Chg,1
            115.7775255,3.49037037,CC_Chg,1
            118.5017026,3.49037037,CC_Chg,1
            122.814983,3.496296296,CC_Chg,1
            126.4472191,3.502222222,CC_Chg,1
            129.8524404,3.508148148,CC_Chg,1
            132.3496027,3.514074074,CC_Chg,1
            135.0737798,3.525925926,CC_Chg,1
            137.1169126,3.525925926,CC_Chg,1
            138.7060159,3.531851852,CC_Chg,1
            141.2031782,3.543703704,CC_Chg,1
            143.4733258,3.54962963,CC_Chg,1
            145.5164586,3.567407407,CC_Chg,1
            147.5595914,3.579259259,CC_Chg,1
            148.9216799,3.591111111,CC_Chg,1
            150.2837684,3.614814815,CC_Chg,1
            151.1918275,3.632592593,CC_Chg,1
            152.0998865,3.656296296,CC_Chg,1
            152.7809308,3.697777778,CC_Chg,1
            153.461975,3.733333333,CC_Chg,1
            153.9160045,3.792592593,CC_Chg,1
            154.3700341,3.84,CC_Chg,1
            154.5970488,3.881481481,CC_Chg,1
            154.8240636,3.934814815,CC_Chg,1
            155.0510783,3.97037037,CC_Chg,1
            155.2780931,4.017777778,CC_Chg,1
            155.5051078,4.059259259,CC_Chg,1
            156.6401816,4.100740741,CC_Chg,1
            0.227014756,4.071111111,CC_DChg,2
            0.454029512,3.685925926,CC_DChg,2
            0.454029512,3.54962963,CC_DChg,2
            0.681044268,3.502222222,CC_DChg,2
            1.13507378,3.466666667,CC_DChg,2
            1.589103292,3.437037037,CC_DChg,2
            2.724177072,3.419259259,CC_DChg,2
            4.313280363,3.401481481,CC_DChg,2
            6.129398411,3.395555556,CC_DChg,2
            19.52326901,3.395555556,CC_DChg,2
            33.37116913,3.395555556,CC_DChg,2
            48.58115778,3.395555556,CC_DChg,2
            52.44040863,3.38962963,CC_DChg,2
            57.2077185,3.395555556,CC_DChg,2
            63.79114642,3.38962963,CC_DChg,2
            72.87173666,3.38962963,CC_DChg,2
            80.81725312,3.38962963,CC_DChg,2
            86.49262202,3.38962963,CC_DChg,2
            91.94097616,3.383703704,CC_DChg,2
            95.11918275,3.377777778,CC_DChg,2
            98.52440409,3.383703704,CC_DChg,2
            101.9296254,3.377777778,CC_DChg,2
            104.4267877,3.377777778,CC_DChg,2
            107.8320091,3.371851852,CC_DChg,2
            110.7832009,3.365925926,CC_DChg,2
            113.9614075,3.36,CC_DChg,2
            117.5936436,3.354074074,CC_DChg,2
            120.7718502,3.342222222,CC_DChg,2
            123.9500568,3.336296296,CC_DChg,2
            126.6742338,3.33037037,CC_DChg,2
            129.1713961,3.324444444,CC_DChg,2
            131.4415437,3.318518519,CC_DChg,2
            133.4846765,3.318518519,CC_DChg,2
            136.2088536,3.306666667,CC_DChg,2
            138.2519864,3.300740741,CC_DChg,2
            140.2951192,3.288888889,CC_DChg,2
            141.6572077,3.277037037,CC_DChg,2
            143.0192963,3.265185185,CC_DChg,2
            144.15437,3.247407407,CC_DChg,2
            145.0624291,3.211851852,CC_DChg,2
            145.7434733,3.182222222,CC_DChg,2
            146.4245176,3.140740741,CC_DChg,2
            147.1055619,3.081481481,CC_DChg,2
            147.7866061,3.022222222,CC_DChg,2
            148.6946652,2.957037037,CC_DChg,2
            149.6027242,2.891851852,CC_DChg,2
            150.2837684,2.820740741,CC_DChg,2
            151.1918275,2.755555556,CC_DChg,2
            151.8728717,2.696296296,CC_DChg,2
        """
        )

        half_cell = (
            pd.read_csv(
                half_cell_data,
                skiprows=2,
                names=["specific_capacity", "voltage", "direction", "id"],
            )
            .drop(columns=["id"])
            .assign(
                direction=lambda x: x["direction"].apply(
                    lambda y: (
                        "discharge"
                        if "CC_DChg" in y
                        else "charge" if "CC_Chg" in y else None
                    )
                ),
            )
        )

        self.material = CathodeMaterial(
            name="LFP",
            reference="Li/Li+",
            specific_cost=6.00,
            density=3.6,
            specific_capacity_curves=half_cell,
        )

        self.material2 = CathodeMaterial(
            name="LFP",
            reference="Li/Li+",
            specific_cost=6.00,
            density=3.6,
            specific_capacity_curves=half_cell,
            voltage_cutoff=4.0,
            reversible_capacity_scaling=0.5,
        )

    def test_instantiation(self):
        """
        Test instantiation
        """
        self.assertTrue(isinstance(self.material, CathodeMaterial))
        self.assertEqual(self.material.voltage_cutoff_range, (3.7, 4.1))

        figure1 = self.material.plot_specific_capacity_curve()
        figure2 = self.material.plot_underlying_specific_capacity_curves()

        # figure1.show()
        # figure2.show()

    def test_serialization(self):
        serialized = self.material.serialize()
        deserialized = CathodeMaterial.deserialize(serialized)
        self.assertEqual(self.material, deserialized)

    def test_equality(self):
        self.assertTrue(self.material == self.material)
        self.assertTrue(self.material != self.material2)

    def test_extrapolation_window_setter(self):

        self.material.extrapolation_window = 0.5
        self.assertEqual(self.material.extrapolation_window, 0.5)
        self.assertEqual(self.material.voltage_cutoff_range, (3.6, 4.1))

    def test_voltage_setter(self):
        """
        Test voltage setter
        """
        self.material.voltage_cutoff = 4.0

        data = self.material.specific_capacity_curve
        figure = self.material.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].max(), 10), 4.0)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            3.59,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 2.7
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            155.19,
        )

        # figure.show()

    def test_from_database(self):
        self.material = CathodeMaterial.from_database("LFP")
        self.assertTrue(isinstance(self.material, CathodeMaterial))

    def test_irreversible_capacity_scaling(self):
        """
        Test irreversible capacity scaling
        """
        self.material.voltage_cutoff = 4
        self.material.irreversible_capacity_scaling = 0.5

        data = self.material.specific_capacity_curve
        figure = self.material.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].max(), 10), 4.0)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            1.79,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 2.7
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            77.6,
        )

        # figure.show()

    def test_reversible_capacity_scaling(self):
        """
        Test reversible capacity scaling
        """
        self.material.voltage_cutoff = 4
        self.material.reversible_capacity_scaling = 0.5

        data = self.material.specific_capacity_curve
        figure = self.material.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].max(), 10), 4)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            79.39,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 2.7
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            155.19,
        )

        # figure.show()

    def test_material2(self):

        data = self.material2.specific_capacity_curve
        figure = self.material2.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].max(), 10), 4)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            79.39,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 2.7
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            155.19,
        )

        # figure.show()

    def test_switching_values(self):
        """
        Test switching values
        """
        self.material.voltage_cutoff = 4.0
        self.material.reversible_capacity_scaling = 0.5
        self.material.irreversible_capacity_scaling = 0.5
        self.material.reversible_capacity_scaling = 0.2
        self.material.irreversible_capacity_scaling = 0.2
        self.material.voltage_cutoff = 4.1
        self.material.voltage_cutoff = 4.0
        self.material.reversible_capacity_scaling = 1
        self.material.irreversible_capacity_scaling = 1

        data = self.material.specific_capacity_curve

        self.assertEqual(round(data["Voltage (V)"].max(), 10), 4.0)
        
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            3.59,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 2.7
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            155.19,
        )


class TestNMMMultiCurve(unittest.TestCase):

    def setUp(self):

        half_cell_data_1 = StringIO(
            """
            Specific Capacity (mAh/g),Voltage (V),Step Name,Step_ID
            0,2.925467626,CC_Chg,1
            0.93676815,2.908201439,CC_Chg,1
            2.43559719,2.908201439,CC_Chg,1
            4.121779859,2.915107914,CC_Chg,1
            7.119437939,2.932374101,CC_Chg,1
            10.49180328,2.94618705,CC_Chg,1
            12.92740047,2.956546763,CC_Chg,1
            16.11241218,2.966906475,CC_Chg,1
            20.6088993,2.987625899,CC_Chg,1
            24.91803279,3.008345324,CC_Chg,1
            27.16627635,3.022158273,CC_Chg,1
            29.78922717,3.046330935,CC_Chg,1
            32.97423888,3.06705036,CC_Chg,1
            35.40983607,3.091223022,CC_Chg,1
            38.40749415,3.118848921,CC_Chg,1
            41.03044496,3.143021583,CC_Chg,1
            44.4028103,3.170647482,CC_Chg,1
            47.21311475,3.187913669,CC_Chg,1
            49.64871194,3.212086331,CC_Chg,1
            51.8969555,3.23971223,CC_Chg,1
            56.01873536,3.281151079,CC_Chg,1
            59.76580796,3.322589928,CC_Chg,1
            62.95081967,3.353669065,CC_Chg,1
            65.76112412,3.384748201,CC_Chg,1
            68.7587822,3.415827338,CC_Chg,1
            71.94379391,3.446906475,CC_Chg,1
            74.56674473,3.477985612,CC_Chg,1
            77.37704918,3.515971223,CC_Chg,1
            79.81264637,3.550503597,CC_Chg,1
            82.24824356,3.585035971,CC_Chg,1
            85.6206089,3.616115108,CC_Chg,1
            88.99297424,3.64028777,CC_Chg,1
            91.99063232,3.667913669,CC_Chg,1
            94.9882904,3.702446043,CC_Chg,1
            97.42388759,3.736978417,CC_Chg,1
            99.85948478,3.754244604,CC_Chg,1
            102.295082,3.788776978,CC_Chg,1
            104.9180328,3.82676259,CC_Chg,1
            107.35363,3.857841727,CC_Chg,1
            109.6018735,3.892374101,CC_Chg,1
            111.8501171,3.923453237,CC_Chg,1
            114.2857143,3.964892086,CC_Chg,1
            116.9086651,4.002877698,CC_Chg,1
            119.5316159,4.044316547,CC_Chg,1
            122.1545667,4.099568345,CC_Chg,1
            124.5901639,4.103021583,CC_Chg,1
            0,4.099568345,CC_DChg,2
            0.74941452,4.061582734,CC_DChg,2
            2.43559719,4.023597122,CC_DChg,2
            4.683840749,3.975251799,CC_DChg,2
            6.932084309,3.930359712,CC_DChg,2
            9.180327869,3.892374101,CC_DChg,2
            12.36533958,3.847482014,CC_DChg,2
            14.80093677,3.809496403,CC_DChg,2
            16.8618267,3.771510791,CC_DChg,2
            19.67213115,3.740431655,CC_DChg,2
            22.29508197,3.705899281,CC_DChg,2
            25.10538642,3.671366906,CC_DChg,2
            28.1030445,3.636834532,CC_DChg,2
            30.72599532,3.602302158,CC_DChg,2
            33.34894614,3.585035971,CC_DChg,2
            35.5971897,3.564316547,CC_DChg,2
            38.03278689,3.53323741,CC_DChg,2
            40.46838407,3.502158273,CC_DChg,2
            42.71662763,3.467625899,CC_DChg,2
            44.96487119,3.436546763,CC_DChg,2
            47.02576112,3.408920863,CC_DChg,2
            49.64871194,3.384748201,CC_DChg,2
            52.64637002,3.353669065,CC_DChg,2
            54.89461358,3.326043165,CC_DChg,2
            57.5175644,3.294964029,CC_DChg,2
            59.57845433,3.270791367,CC_DChg,2
            62.76346604,3.236258993,CC_DChg,2
            65.19906323,3.205179856,CC_DChg,2
            67.82201405,3.174100719,CC_DChg,2
            70.07025761,3.143021583,CC_DChg,2
            72.69320843,3.118848921,CC_DChg,2
            74.75409836,3.094676259,CC_DChg,2
            77.18969555,3.070503597,CC_DChg,2
            78.87587822,3.035971223,CC_DChg,2
            80.74941452,3.001438849,CC_DChg,2
            83.37236534,2.956546763,CC_DChg,2
            85.05854801,2.915107914,CC_DChg,2
            86.93208431,2.88057554,CC_DChg,2
            88.80562061,2.846043165,CC_DChg,2
            91.05386417,2.818417266,CC_DChg,2
            93.30210773,2.794244604,CC_DChg,2
            95.36299766,2.776978417,CC_DChg,2
            97.79859485,2.756258993,CC_DChg,2
            100.4215457,2.735539568,CC_DChg,2
            102.4824356,2.711366906,CC_DChg,2
            104.1686183,2.68028777,CC_DChg,2
            105.8548009,2.642302158,CC_DChg,2
            107.9156909,2.590503597,CC_DChg,2
            109.2271663,2.535251799,CC_DChg,2
            110.9133489,2.486906475,CC_DChg,2
            112.5995316,2.431654676,CC_DChg,2
            114.0983607,2.376402878,CC_DChg,2
            115.2224824,2.310791367,CC_DChg,2
            116.1592506,2.245179856,CC_DChg,2
            117.2833724,2.193381295,CC_DChg,2
            117.6580796,2.145035971,CC_DChg,2
            118.4074941,2.086330935,CC_DChg,2
            119.7189696,2.037985612,CC_DChg,2
            121.2177986,1.996546763,CC_DChg,2
        """
        )

        half_cell_data_2 = StringIO(
            """
            Specific Capacity (mAh/g),Voltage (V),Step Name,Step_ID
            0,2.873669065,CC_Chg,1
            1.12412178,2.863309353,CC_Chg,1
            2.24824356,2.86676259,CC_Chg,1
            3.55971897,2.877122302,CC_Chg,1
            5.620608899,2.894388489,CC_Chg,1
            8.805620609,2.915107914,CC_Chg,1
            12.17798595,2.932374101,CC_Chg,1
            16.67447307,2.96,CC_Chg,1
            20.04683841,2.980719424,CC_Chg,1
            23.79391101,3.004892086,CC_Chg,1
            28.1030445,3.032517986,CC_Chg,1
            31.66276347,3.073956835,CC_Chg,1
            34.28571429,3.101582734,CC_Chg,1
            37.65807963,3.132661871,CC_Chg,1
            40.28103044,3.156834532,CC_Chg,1
            43.65339578,3.187913669,CC_Chg,1
            46.2763466,3.212086331,CC_Chg,1
            49.46135831,3.243165468,CC_Chg,1
            52.08430913,3.274244604,CC_Chg,1
            54.51990632,3.298417266,CC_Chg,1
            56.95550351,3.322589928,CC_Chg,1
            59.76580796,3.34676259,CC_Chg,1
            62.76346604,3.377841727,CC_Chg,1
            65.57377049,3.408920863,CC_Chg,1
            68.7587822,3.44,CC_Chg,1
            71.94379391,3.464172662,CC_Chg,1
            74.75409836,3.491798561,CC_Chg,1
            78.50117096,3.53323741,CC_Chg,1
            81.31147541,3.578129496,CC_Chg,1
            83.93442623,3.598848921,CC_Chg,1
            86.93208431,3.62647482,CC_Chg,1
            90.30444965,3.654100719,CC_Chg,1
            93.67681499,3.688633094,CC_Chg,1
            96.67447307,3.726618705,CC_Chg,1
            99.67213115,3.761151079,CC_Chg,1
            102.4824356,3.802589928,CC_Chg,1
            104.9180328,3.830215827,CC_Chg,1
            106.9789227,3.861294964,CC_Chg,1
            109.4145199,3.895827338,CC_Chg,1
            111.4754098,3.923453237,CC_Chg,1
            113.911007,3.964892086,CC_Chg,1
            116.1592506,3.995971223,CC_Chg,1
            118.5948478,4.023597122,CC_Chg,1
            121.5925059,4.065035971,CC_Chg,1
            124.028103,4.103021583,CC_Chg,1
            126.8384075,4.134100719,CC_Chg,1
            129.6487119,4.154820144,CC_Chg,1
            132.2716628,4.175539568,CC_Chg,1
            135.0819672,4.189352518,CC_Chg,1
            138.8290398,4.19971223,CC_Chg,1
            142.2014052,4.216978417,CC_Chg,1
            144.824356,4.234244604,CC_Chg,1
            146.8852459,4.254964029,CC_Chg,1
            150.8196721,4.251510791,CC_Chg,1
            0,4.254964029,CC_DChg,2
            0.37470726,4.220431655,CC_DChg,2
            1.31147541,4.189352518,CC_DChg,2
            2.62295082,4.154820144,CC_DChg,2
            4.496487119,4.123741007,CC_DChg,2
            7.119437939,4.085755396,CC_DChg,2
            9.742388759,4.061582734,CC_DChg,2
            11.80327869,4.037410072,CC_DChg,2
            14.23887588,4.016690647,CC_DChg,2
            16.67447307,3.99942446,CC_DChg,2
            18.92271663,3.982158273,CC_DChg,2
            20.98360656,3.964892086,CC_DChg,2
            22.85714286,3.947625899,CC_DChg,2
            24.54332553,3.923453237,CC_DChg,2
            27.35362998,3.892374101,CC_DChg,2
            29.9765808,3.854388489,CC_DChg,2
            32.78688525,3.82676259,CC_DChg,2
            35.22248244,3.799136691,CC_DChg,2
            37.470726,3.764604317,CC_DChg,2
            40.09367681,3.73352518,CC_DChg,2
            42.529274,3.702446043,CC_DChg,2
            45.15222482,3.667913669,CC_DChg,2
            47.58782201,3.636834532,CC_DChg,2
            50.0234192,3.612661871,CC_DChg,2
            53.02107728,3.581582734,CC_DChg,2
            55.08196721,3.564316547,CC_DChg,2
            57.33021077,3.540143885,CC_DChg,2
            60.14051522,3.509064748,CC_DChg,2
            63.1381733,3.474532374,CC_DChg,2
            65.94847775,3.433093525,CC_DChg,2
            68.94613583,3.402014388,CC_DChg,2
            71.56908665,3.377841727,CC_DChg,2
            74.94145199,3.343309353,CC_DChg,2
            77.75175644,3.315683453,CC_DChg,2
            80,3.291510791,CC_DChg,2
            82.43559719,3.263884892,CC_DChg,2
            85.24590164,3.232805755,CC_DChg,2
            87.68149883,3.208633094,CC_DChg,2
            89.92974239,3.184460432,CC_DChg,2
            91.99063232,3.163741007,CC_DChg,2
            94.42622951,3.139568345,CC_DChg,2
            96.8618267,3.118848921,CC_DChg,2
            99.48477752,3.087769784,CC_DChg,2
            101.9203747,3.056690647,CC_DChg,2
            104.1686183,3.029064748,CC_DChg,2
            106.4168618,2.994532374,CC_DChg,2
            109.0398126,2.953093525,CC_DChg,2
            111.2880562,2.915107914,CC_DChg,2
            113.1615925,2.88057554,CC_DChg,2
            115.4098361,2.846043165,CC_DChg,2
            117.8454333,2.808057554,CC_DChg,2
            120.6557377,2.780431655,CC_DChg,2
            123.2786885,2.763165468,CC_DChg,2
            125.7142857,2.742446043,CC_DChg,2
            127.9625293,2.718273381,CC_DChg,2
            130.0234192,2.690647482,CC_DChg,2
            131.7096019,2.659568345,CC_DChg,2
            133.0210773,2.625035971,CC_DChg,2
            134.5199063,2.583597122,CC_DChg,2
            135.6440281,2.549064748,CC_DChg,2
            136.7681499,2.504172662,CC_DChg,2
            137.8922717,2.459280576,CC_DChg,2
            139.2037471,2.404028777,CC_DChg,2
            140.1405152,2.341870504,CC_DChg,2
            141.264637,2.286618705,CC_DChg,2
            142.2014052,2.241726619,CC_DChg,2
            142.9508197,2.183021583,CC_DChg,2
            143.7002342,2.127769784,CC_DChg,2
            144.4496487,2.086330935,CC_DChg,2
            145.5737705,2.048345324,CC_DChg,2
            147.2599532,2,CC_DChg,2
        """
        )

        half_cell_data_3 = StringIO(
            """
            Specific Capacity (mAh/g),Voltage (V),Step Name,Step_ID
            0,2.839136691,CC_Chg,1
            2.06088993,2.842589928,CC_Chg,1
            4.309133489,2.85294964,CC_Chg,1
            7.681498829,2.88057554,CC_Chg,1
            10.49180328,2.904748201,CC_Chg,1
            12.92740047,2.932374101,CC_Chg,1
            16.29976581,2.956546763,CC_Chg,1
            19.11007026,2.97381295,CC_Chg,1
            21.17096019,2.991079137,CC_Chg,1
            23.98126464,3.018705036,CC_Chg,1
            26.97892272,3.03942446,CC_Chg,1
            29.60187354,3.06705036,CC_Chg,1
            32.22482436,3.094676259,CC_Chg,1
            34.66042155,3.115395683,CC_Chg,1
            36.90866511,3.139568345,CC_Chg,1
            39.71896956,3.167194245,CC_Chg,1
            42.529274,3.191366906,CC_Chg,1
            45.71428571,3.218992806,CC_Chg,1
            48.71194379,3.23971223,CC_Chg,1
            52.27166276,3.277697842,CC_Chg,1
            55.08196721,3.305323741,CC_Chg,1
            58.26697892,3.336402878,CC_Chg,1
            61.63934426,3.374388489,CC_Chg,1
            64.44964871,3.398561151,CC_Chg,1
            67.07259953,3.415827338,CC_Chg,1
            70.25761124,3.450359712,CC_Chg,1
            73.06791569,3.481438849,CC_Chg,1
            75.87822014,3.512517986,CC_Chg,1
            78.68852459,3.54705036,CC_Chg,1
            81.49882904,3.585035971,CC_Chg,1
            85.24590164,3.612661871,CC_Chg,1
            88.05620609,3.64028777,CC_Chg,1
            91.05386417,3.664460432,CC_Chg,1
            93.86416862,3.695539568,CC_Chg,1
            96.67447307,3.730071942,CC_Chg,1
            99.29742389,3.764604317,CC_Chg,1
            102.1077283,3.806043165,CC_Chg,1
            105.29274,3.837122302,CC_Chg,1
            108.1030445,3.878561151,CC_Chg,1
            111.8501171,3.930359712,CC_Chg,1
            115.2224824,3.978705036,CC_Chg,1
            118.0327869,4.020143885,CC_Chg,1
            121.030445,4.058129496,CC_Chg,1
            124.4028103,4.10647482,CC_Chg,1
            127.2131148,4.134100719,CC_Chg,1
            130.3981265,4.158273381,CC_Chg,1
            134.3325527,4.182446043,CC_Chg,1
            137.704918,4.192805755,CC_Chg,1
            140.5152225,4.206618705,CC_Chg,1
            143.8875878,4.227338129,CC_Chg,1
            147.2599532,4.254964029,CC_Chg,1
            149.5081967,4.282589928,CC_Chg,1
            152.1311475,4.310215827,CC_Chg,1
            155.1288056,4.348201439,CC_Chg,1
            159.8126464,4.355107914,CC_Chg,1
            0,4.348201439,CC_DChg,2
            0.74941452,4.303309353,CC_DChg,2
            1.8735363,4.258417266,CC_DChg,2
            3.55971897,4.216978417,CC_DChg,2
            4.683840749,4.185899281,CC_DChg,2
            6.932084309,4.141007194,CC_DChg,2
            8.992974239,4.109928058,CC_DChg,2
            11.42857143,4.075395683,CC_DChg,2
            14.42622951,4.044316547,CC_DChg,2
            18.17330211,4.01323741,CC_DChg,2
            20.79625293,3.989064748,CC_DChg,2
            23.60655738,3.975251799,CC_DChg,2
            26.79156909,3.951079137,CC_DChg,2
            29.22716628,3.923453237,CC_DChg,2
            32.03747073,3.892374101,CC_DChg,2
            34.47306792,3.861294964,CC_DChg,2
            37.470726,3.823309353,CC_DChg,2
            39.90632319,3.799136691,CC_DChg,2
            42.34192037,3.768057554,CC_DChg,2
            45.52693208,3.730071942,CC_DChg,2
            49.27400468,3.685179856,CC_DChg,2
            52.45901639,3.647194245,CC_DChg,2
            55.08196721,3.616115108,CC_DChg,2
            59.01639344,3.574676259,CC_DChg,2
            62.76346604,3.540143885,CC_DChg,2
            66.32318501,3.498705036,CC_DChg,2
            69.32084309,3.457266187,CC_DChg,2
            72.5058548,3.422733813,CC_DChg,2
            75.50351288,3.391654676,CC_DChg,2
            78.31381733,3.36057554,CC_DChg,2
            81.68618267,3.33294964,CC_DChg,2
            85.99531616,3.284604317,CC_DChg,2
            89.55503513,3.250071942,CC_DChg,2
            92.92740047,3.208633094,CC_DChg,2
            97.61124122,3.163741007,CC_DChg,2
            100.9836066,3.132661871,CC_DChg,2
            105.29274,3.084316547,CC_DChg,2
            108.6651054,3.03942446,CC_DChg,2
            112.9742389,2.984172662,CC_DChg,2
            115.7845433,2.939280576,CC_DChg,2
            118.969555,2.887482014,CC_DChg,2
            121.5925059,2.849496403,CC_DChg,2
            124.4028103,2.804604317,CC_DChg,2
            127.0257611,2.770071942,CC_DChg,2
            129.8360656,2.742446043,CC_DChg,2
            133.2084309,2.714820144,CC_DChg,2
            135.4566745,2.687194245,CC_DChg,2
            137.704918,2.645755396,CC_DChg,2
            140.5152225,2.590503597,CC_DChg,2
            143.1381733,2.514532374,CC_DChg,2
            145.1990632,2.438561151,CC_DChg,2
            146.6978923,2.369496403,CC_DChg,2
            148.1967213,2.300431655,CC_DChg,2
            149.5081967,2.234820144,CC_DChg,2
            150.8196721,2.165755396,CC_DChg,2
            151.9437939,2.110503597,CC_DChg,2
            153.6299766,2.055251799,CC_DChg,2
            156.0655738,2.003453237,CC_DChg,2
        """
        )

        half_cell_1 = (
            pd.read_csv(
                half_cell_data_1,
                skiprows=2,
                names=["specific_capacity", "voltage", "direction", "id"],
            )
            .drop(columns=["id"])
            .assign(
                direction=lambda x: x["direction"].apply(
                    lambda y: (
                        "discharge"
                        if "CC_DChg" in y
                        else "charge" if "CC_Chg" in y else None
                    )
                ),
            )
        )

        half_cell_2 = (
            pd.read_csv(
                half_cell_data_2,
                skiprows=2,
                names=["specific_capacity", "voltage", "direction", "id"],
            )
            .drop(columns=["id"])
            .assign(
                direction=lambda x: x["direction"].apply(
                    lambda y: (
                        "discharge"
                        if "CC_DChg" in y
                        else "charge" if "CC_Chg" in y else None
                    )
                ),
            )
        )

        half_cell_3 = (
            pd.read_csv(
                half_cell_data_3,
                skiprows=2,
                names=["specific_capacity", "voltage", "direction", "id"],
            )
            .drop(columns=["id"])
            .assign(
                direction=lambda x: x["direction"].apply(
                    lambda y: (
                        "discharge"
                        if "CC_DChg" in y
                        else "charge" if "CC_Chg" in y else None
                    )
                ),
            )
        )

        self.material = CathodeMaterial(
            name="NMM",
            specific_capacity_curves=[half_cell_1, half_cell_2, half_cell_3],
            reference="Na/Na+",
            density=4.4,
            specific_cost=1.1,
        )

    def test_instantiation(self):
        self.assertIsInstance(self.material, CathodeMaterial)
        self.assertTrue(self.material.voltage_cutoff_range == (3.7, 4.36))

    def test_voltage_setter_extrapolate(self):

        self.material.voltage_cutoff = 4.1
        data = self.material.specific_capacity_curve
        figure = self.material.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].max(), 10), 4.1)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            1.24,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 2
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            122.46,
        )

        # figure.show()

    def test_voltage_setter_interpolate(self):

        self.material.voltage_cutoff = 4.2
        data = self.material.specific_capacity_curve
        figure = self.material.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].max(), 2), 4.20)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            3.49,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 2.0
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            141.33,
        )

        # figure.show()


class TestHardCarbon(unittest.TestCase):

    def setUp(self):

        half_cell_data = StringIO(
            """
            Specific Capacity (mAh/g),Voltage (V),Step Name,Step_ID
            0,2.063123515,CC_DChg,1
            0,2.023708432,CC_DChg,1
            0,1.966775534,CC_DChg,1
            0,1.918601544,CC_DChg,1
            0,1.877544166,CC_DChg,1
            0,1.839771378,CC_DChg,1
            0,1.80199859,CC_DChg,1
            0,1.760941211,CC_DChg,1
            0,1.721526128,CC_DChg,1
            0,1.681782586,CC_DChg,1
            0,1.642695962,CC_DChg,1
            0,1.604923174,CC_DChg,1
            0,1.560581205,CC_DChg,1
            0,1.521166122,CC_DChg,1
            0,1.480108744,CC_DChg,1
            0,1.442335956,CC_DChg,1
            0,1.404563168,CC_DChg,1
            0,1.36350579,CC_DChg,1
            0.112145985,1.313415788,CC_DChg,1
            0.627917606,1.262778355,CC_DChg,1
            2.101550812,1.223089556,CC_DChg,1
            5.196180543,1.17792644,CC_DChg,1
            8.732900235,1.131942176,CC_DChg,1
            12.26961993,1.085957913,CC_DChg,1
            15.36424966,1.047090261,CC_DChg,1
            18.45887939,1.002200861,CC_DChg,1
            21.99559908,0.95539545,CC_DChg,1
            25.53231877,0.907768891,CC_DChg,1
            29.06903847,0.862605775,CC_DChg,1
            32.60575816,0.819084954,CC_DChg,1
            36.14247785,0.778027576,CC_DChg,1
            39.67919754,0.73943364,CC_DChg,1
            43.6580072,0.696733967,CC_DChg,1
            48.07890681,0.654691211,CC_DChg,1
            52.49980643,0.616589964,CC_DChg,1
            57.36279601,0.579583581,CC_DChg,1
            62.66787555,0.539621066,CC_DChg,1
            67.53086512,0.503600059,CC_DChg,1
            72.3938547,0.466812648,CC_DChg,1
            77.69893424,0.424660407,CC_DChg,1
            83.00401378,0.38415046,CC_DChg,1
            88.30909332,0.343093082,CC_DChg,1
            93.61417285,0.305320294,CC_DChg,1
            98.91925239,0.268094938,CC_DChg,1
            104.2243319,0.235249035,CC_DChg,1
            109.5294115,0.205687723,CC_DChg,1
            114.834491,0.181053296,CC_DChg,1
            120.1395705,0.161893186,CC_DChg,1
            125.4446501,0.145470235,CC_DChg,1
            130.7497296,0.130689578,CC_DChg,1
            138.7073489,0.10550772,CC_DChg,1
            144.0124285,0.100580834,CC_DChg,1
            149.317508,0.098938539,CC_DChg,1
            154.6225876,0.096201381,CC_DChg,1
            159.9276671,0.09163945,CC_DChg,1
            165.2327466,0.085800178,CC_DChg,1
            170.5378262,0.079778429,CC_DChg,1
            175.8429057,0.076493839,CC_DChg,1
            181.1479852,0.073756681,CC_DChg,1
            186.4530648,0.072661817,CC_DChg,1
            191.7581443,0.069924659,CC_DChg,1
            197.0632239,0.068282363,CC_DChg,1
            202.3683034,0.066092637,CC_DChg,1
            207.6733829,0.066092637,CC_DChg,1
            212.9784625,0.065545205,CC_DChg,1
            218.283542,0.062808046,CC_DChg,1
            223.5886216,0.061713183,CC_DChg,1
            228.8937011,0.059523456,CC_DChg,1
            234.1987806,0.059523456,CC_DChg,1
            239.5038602,0.059523456,CC_DChg,1
            244.8089397,0.057881161,CC_DChg,1
            250.1140192,0.052954276,CC_DChg,1
            255.4190988,0.052954276,CC_DChg,1
            260.7241783,0.053501707,CC_DChg,1
            266.0292579,0.054596571,CC_DChg,1
            271.3343374,0.052954276,CC_DChg,1
            276.6394169,0.049122254,CC_DChg,1
            281.9444965,0.046385095,CC_DChg,1
            287.249576,0.046385095,CC_DChg,1
            292.5546556,0.045837663,CC_DChg,1
            297.8597351,0.039815914,CC_DChg,1
            303.1648146,0.039815914,CC_DChg,1
            308.4698942,0.039815914,CC_DChg,1
            313.7749737,0.033246734,CC_DChg,1
            319.0800533,0.033246734,CC_DChg,1
            324.3851328,0.029962144,CC_DChg,1
            329.6902123,0.026677553,CC_DChg,1
            334.9952919,0.024487827,CC_DChg,1
            340.3003714,0.020108373,CC_DChg,1
            345.6054509,0.014634056,CC_DChg,1
            350.9105305,0.009159739,CC_DChg,1
            356.21561,0.002590558,CC_DChg,1
            359.7523297,-0.001241464,CC_DChg,1
            1.65946085,0.031057007,CC_Chg,2
            6.964540389,0.039815914,CC_Chg,2
            12.26961993,0.048574822,CC_Chg,2
            17.57469947,0.055691434,CC_Chg,2
            22.879779,0.062260615,CC_Chg,2
            28.18485854,0.066092637,CC_Chg,2
            33.48993808,0.071566954,CC_Chg,2
            38.79501762,0.072661817,CC_Chg,2
            44.10009716,0.075946407,CC_Chg,2
            49.4051767,0.079230998,CC_Chg,2
            54.71025624,0.079230998,CC_Chg,2
            60.01533578,0.082515588,CC_Chg,2
            65.32041531,0.085800178,CC_Chg,2
            70.62549485,0.085800178,CC_Chg,2
            75.93057439,0.085800178,CC_Chg,2
            81.23565393,0.085800178,CC_Chg,2
            86.54073347,0.085800178,CC_Chg,2
            91.84581301,0.085800178,CC_Chg,2
            97.15089255,0.087442473,CC_Chg,2
            102.4559721,0.090727064,CC_Chg,2
            107.7610516,0.092369359,CC_Chg,2
            113.0661312,0.092369359,CC_Chg,2
            118.3712107,0.092369359,CC_Chg,2
            123.6762902,0.092369359,CC_Chg,2
            128.9813698,0.092369359,CC_Chg,2
            134.2864493,0.095653949,CC_Chg,2
            139.5915289,0.100033403,CC_Chg,2
            144.8966084,0.100033403,CC_Chg,2
            150.2016879,0.098938539,CC_Chg,2
            155.5067675,0.096748812,CC_Chg,2
            160.811847,0.100580834,CC_Chg,2
            166.1169266,0.104960288,CC_Chg,2
            171.4220061,0.10550772,CC_Chg,2
            176.7270856,0.106055151,CC_Chg,2
            182.0321652,0.111529469,CC_Chg,2
            187.3372447,0.112624332,CC_Chg,2
            192.6423242,0.118646081,CC_Chg,2
            197.9474038,0.124120398,CC_Chg,2
            203.2524833,0.132879305,CC_Chg,2
            208.5575629,0.142733076,CC_Chg,2
            213.8626424,0.1569663,CC_Chg,2
            219.1677219,0.17284182,CC_Chg,2
            224.4728015,0.193644225,CC_Chg,2
            229.777881,0.220468379,CC_Chg,2
            235.0829606,0.253861713,CC_Chg,2
            239.9459501,0.29075861,CC_Chg,2
            244.3668497,0.328859857,CC_Chg,2
            248.7877494,0.365647268,CC_Chg,2
            253.208649,0.40571927,CC_Chg,2
            257.6295486,0.447105107,CC_Chg,2
            262.0504482,0.487177108,CC_Chg,2
            266.0292579,0.526756421,CC_Chg,2
            270.0080675,0.564693438,CC_Chg,2
            273.9868772,0.601480849,CC_Chg,2
            277.9656868,0.640895932,CC_Chg,2
            281.9444965,0.676205278,CC_Chg,2
            285.9233061,0.717098426,CC_Chg,2
            290.3442057,0.755856591,CC_Chg,2
            294.7651054,0.801183937,CC_Chg,2
            298.743915,0.839613643,CC_Chg,2
            302.2806347,0.877386431,CC_Chg,2
            305.8173544,0.916801514,CC_Chg,2
            308.9119841,0.951837144,CC_Chg,2
            312.0066139,0.990704795,CC_Chg,2
            315.1012436,1.031762173,CC_Chg,2
            317.7537834,1.07227212,CC_Chg,2
            320.4063231,1.11387693,CC_Chg,2
            322.6167729,1.154934308,CC_Chg,2
            324.8272228,1.20037114,CC_Chg,2
            326.1534926,1.250187426,CC_Chg,2
            327.4797625,1.303562018,CC_Chg,2
            327.9218525,1.3602212,CC_Chg,2
            328.9533957,1.454379454,CC_Chg,2
            328.8060324,1.406205463,CC_Chg,2
            329.6902123,1.596711698,CC_Chg,2
            329.8375756,1.548537708,CC_Chg,2
            329.2481224,1.517881532,CC_Chg,2
            330.7217556,1.920791271,CC_Chg,2
            330.5743923,1.86933269,CC_Chg,2
            330.5743923,1.829917607,CC_Chg,2
            330.5743923,1.790502524,CC_Chg,2
            330.5743923,1.754372031,CC_Chg,2
            330.1323023,1.714956948,CC_Chg,2
            330.1323023,1.675541865,CC_Chg,2
            330.1323023,1.636126781,CC_Chg,2
            331.0164822,1.984293349,CC_Chg,2
        """
        )

        half_cell = (
            pd.read_csv(
                half_cell_data,
                skiprows=2,
                names=["specific_capacity", "voltage", "direction", "id"],
            )
            .drop(columns=["id"])
            .assign(
                direction=lambda x: x["direction"].apply(
                    lambda y: (
                        "discharge"
                        if "CC_DChg" in y
                        else "charge" if "CC_Chg" in y else None
                    )
                ),
            )
        )

        self.material = AnodeMaterial(
            name="Hard Carbon",
            specific_capacity_curves=[half_cell],
            reference="Na/Na+",
            density=1.5,
            specific_cost=7,
        )

    def test_instantiation(self):
        """
        Test instantiation
        """
        self.assertTrue(isinstance(self.material, AnodeMaterial))
        self.assertEqual(self.material.voltage_cutoff_range, (0.05, 0))
        figure = self.material.plot_specific_capacity_curve()

        # figure.show()

    def test_voltage_setter_extrapolate(self):
        """
        Test voltage setter with extrapolation
        """
        self.material.voltage_cutoff = 0
        data = self.material.specific_capacity_curve
        figure = self.material.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].min(), 10), 0)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].max(),
                2,
            ),
            358.61,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 0.0
        )

        # figure.show()

    def test_reversible_capacity_scaling(self):
        """
        Test reversible capacity scaling
        """
        self.material.reversible_capacity_scaling = 0.5
        data = self.material.specific_capacity_curve
        figure = self.material.plot_specific_capacity_curve()

        self.assertEqual(round(data["Voltage (V)"].max(), 2), 2.06)
        self.assertEqual(
            np.round(
                data.query('Direction == "discharge"')[
                    "Specific Capacity (mAh/g)"
                ].min(),
                2,
            ),
            194.24,
        )
        self.assertEqual(
            np.round(data.query('Direction == "discharge"')["Voltage (V)"].min(), 2), 0
        )
        self.assertEqual(
            np.round(
                data.query('Direction == "charge"')["Specific Capacity (mAh/g)"].max(),
                2,
            ),
            359.75,
        )

        # figure.show()


class TestBinder(unittest.TestCase):
    def setUp(self):
        self.name = "PVDF"
        self.specific_cost = 20.0
        self.density = 1.7
        self.color = "#ff0000"
        self.binder = Binder(
            name=self.name,
            specific_cost=self.specific_cost,
            density=self.density,
            color=self.color,
        )

    def test_instantiation(self):
        self.assertIsInstance(self.binder, Binder)
        self.assertEqual(self.binder.name, self.name)
        self.assertEqual(self.binder.specific_cost, self.specific_cost)
        self.assertEqual(self.binder.density, self.density)
        self.assertEqual(self.binder.color, self.color)


class TestConductiveAdditive(unittest.TestCase):
    def setUp(self):
        self.name = "Carbon Black"
        self.specific_cost = 10.0
        self.density = 2.0
        self.color = "#000000"
        self.additive = ConductiveAdditive(
            name=self.name,
            specific_cost=self.specific_cost,
            density=self.density,
            color=self.color,
        )

    def test_instantiation(self):
        self.assertIsInstance(self.additive, ConductiveAdditive)
        self.assertEqual(self.additive.name, self.name)
        self.assertEqual(self.additive.specific_cost, self.specific_cost)
        self.assertEqual(self.additive.density, self.density)
        self.assertEqual(self.additive.color, self.color)







class TestElectrolyteVolumeMassCost(unittest.TestCase):

    def setUp(self):
        self.electrolyte = Electrolyte(
            name="Test Electrolyte",
            density=1.2,  # g/cm^3
            specific_cost=15.0,  # $/kg
            color="#abcdef",
        )

    def test_volume_setter_updates_mass_and_cost(self):
        self.electrolyte.volume = 10.0

        self.assertAlmostEqual(self.electrolyte.volume, 10.0, places=4)
        self.assertAlmostEqual(self.electrolyte.mass, 12.0, places=2)
        self.assertAlmostEqual(self.electrolyte.cost, 0.18, places=2)

    def test_mass_setter_updates_volume_and_cost(self):
        self.electrolyte.mass = 25.0

        self.assertAlmostEqual(self.electrolyte.mass, 25.0, places=2)
        self.assertAlmostEqual(self.electrolyte.volume, 20.8333, places=3)
        self.assertAlmostEqual(self.electrolyte.cost, 0.38, places=2)


if __name__ == "__main__":
    unittest.main()

