"""
"""

import unittest
import filecmp
import os

import numpy as np
import mlx75027_config as mlx


class EPC660ConfigTest(unittest.TestCase):
    def test_import_export(self):
        """
        Test the import and export functions of the CSV files 

        """
        import_file = os.path.join("..", "epc660.csv")
        export_file = "epc660_export.csv"
        if os.path.isfile(export_file):
            os.remove(export_file)

        self.assertTrue(os.path.isfile(import_file))

        reg_dict = mlx.csv_import(import_file)

        mlx.csv_export(export_file, reg_dict)
        self.assertTrue(os.path.isfile(export_file))
        reg_export = mlx.csv_import(export_file)

        for n in reg_dict.keys():
            self.assertEqual(reg_dict[n][2], reg_export[n][2])

        os.remove(export_file)
        return

    def test_mod_frequency(self):
        import_file = os.path.join("..", "epc660.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        mclk = 96.0
        demod_clk = 0.0

        fmod = mlx.epc_calc_mod_freq(reg_dict, mclk, demod_clk)
        self.assertEqual(fmod, mclk/8.0)

        mlx.epc_set_mod_freq(reg_dict, 4.0, mclk)
        fmod_update = mlx.epc_calc_mod_freq(reg_dict, mclk, demod_clk)
        self.assertEqual(fmod_update, 4.0)

        mlx.epc_set_mod_freq(reg_dict, 4.5, mclk)
        fmod_update = mlx.epc_calc_mod_freq(reg_dict, mclk, demod_clk)
        self.assertEqual(fmod_update, 4.8)
        return

    def test_dll_settings(self):
        import_file = os.path.join("..", "epc660.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        mclk = 96.0
        demod_clk = 0.0
        fmod = 24.0

        mlx.epc_set_mod_freq(reg_dict, fmod, mclk)
        phi = mlx.epc_calc_light_phase(reg_dict, mclk, demod_clk)
        self.assertEqual(phi, 0.0)
        dll_values = [0.0, 45.0, 90.0, 135.0, 180.0]
        for phiX in dll_values:
            mlx.epc_setup_light_phase(reg_dict, phiX, mclk, demod_clk)
            phi_calc = mlx.epc_calc_light_phase(reg_dict, mclk, demod_clk)
            self.assertEqual(np.round(phi_calc), phiX)

            # Convert to radians, and set the same value in radians
            rad = phiX * np.pi/180.0
            mlx.epc_setup_light_phase(reg_dict, rad, mclk, demod_clk, True)
            phi_calc = mlx.epc_calc_light_phase(reg_dict, mclk, demod_clk)
            self.assertEqual(np.round(phi_calc), phiX)

        return

    def test_roi(self):
        row_start = 6
        row_end = 125
        col_start = 4
        col_end = 323

        import_file = os.path.join("..", "epc660.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        mclk = 96.0
        demod_clk = 0.0

        mlx.epc_set_roi(reg_dict, col_start, col_end, row_start, row_end)
        nrows, ncols = mlx.epc_calc_img_size(reg_dict)

        self.assertEqual(int(nrows), 240)
        self.assertEqual(int(ncols), 320)

        # Now set the binning options.
        mlx.epc_set_bin_mode(reg_dict, True, True)
        mlx.epc_set_binning(reg_dict, 0, 0)

        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 240)
        self.assertEqual(int(ncols), 320)

        mlx.epc_set_binning(reg_dict, 0, 1)
        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 240)
        self.assertEqual(int(ncols), 160)

        mlx.epc_set_binning(reg_dict, 1, 0)
        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 120)
        self.assertEqual(int(ncols), 320)

        mlx.epc_set_binning(reg_dict, 2, 0)
        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 60)
        self.assertEqual(int(ncols), 320)

        mlx.epc_set_binning(reg_dict, 3, 0)
        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 30)
        self.assertEqual(int(ncols), 320)

        mlx.epc_set_bin_mode(reg_dict, False, True)
        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 240)
        self.assertEqual(int(ncols), 320)

        # No binning
        mlx.epc_set_bin_mode(reg_dict, False, False)

        # Write some ROI values.
        row_start = 6
        row_end = 125
        col_start = 104
        col_end = 323

        # First the columns
        mlx.epc_set_roi(reg_dict, col_start, col_end, row_start, row_end)
        # Verify what we read and write are the same
        cs, ce, rs, re = mlx.epc_calc_roi(reg_dict)
        self.assertEqual(rs, row_start)
        self.assertEqual(re, row_end)
        self.assertEqual(cs, col_start)
        self.assertEqual(ce, col_end)

        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 240)
        self.assertEqual(int(ncols), 220)

        # Write some row settings.
        row_start = 56
        row_end = 105
        mlx.epc_set_roi(reg_dict, col_start, col_end, row_start, row_end)
        cs, ce, rs, re = mlx.epc_calc_roi(reg_dict)
        self.assertEqual(rs, row_start)
        self.assertEqual(re, row_end)
        self.assertEqual(cs, col_start)
        self.assertEqual(ce, col_end)

        nrows, ncols = mlx.epc_calc_img_size(reg_dict)
        self.assertEqual(int(nrows), 100)
        self.assertEqual(int(ncols), 220)
        return

    def test_int_times(self):
        import_file = os.path.join("..", "epc660.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        mclk = 96.0
        demod_clk = 0.0
        # Set no HDR
        hdr = mlx.epc_calc_hdr(reg_dict)
        self.assertFalse(hdr)
        # Set the integration times
        int_times = mlx.epc_calc_int_times(reg_dict, mclk, demod_clk)
        self.assertEqual(np.size(int_times), 1)
        test_times = [0.1, 0.25, 0.5, 0.75, 1.1]
        for tx in test_times:
            mlx.epc_set_int_times(reg_dict, tx, mclk, demod_clk)
            int_time = mlx.epc_calc_int_times(reg_dict, mclk, demod_clk)
            self.assertEqual(tx, np.round(int_time[0], 2))

            mlx.epc_set_int_times(reg_dict, np.array([tx]), mclk, demod_clk)
            int_time = mlx.epc_calc_int_times(reg_dict, mclk, demod_clk)
            self.assertEqual(tx, np.round(int_time[0], 2))

        # HDR
        mlx.epc_set_mode(reg_dict, False, False, True)
        hdr = mlx.epc_calc_hdr(reg_dict)
        self.assertTrue(hdr)
        int_times = mlx.epc_calc_int_times(reg_dict, mclk, demod_clk)
        self.assertEqual(np.size(int_times), 2)

        test_times = [[0.1, 0.2], [0.1, 0.5], [0.1, 1.0]]
        for tx in test_times:
            mlx.epc_set_int_times(reg_dict, tx, mclk, demod_clk)
            int_time = mlx.epc_calc_int_times(reg_dict, mclk, demod_clk)
            self.assertEqual(tx[0], np.round(int_time[0], 2))
            self.assertEqual(tx[1], np.round(int_time[1], 2))
        return

    def test_sequence(self):
        import_file = os.path.join("..", "epc660.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        # Single phase
        seq_base = np.array([0, 1, 2, 3])
        mlx.epc_set_phase_steps(reg_dict, seq_base)
        seq = mlx.epc_calc_phase_steps(reg_dict)
        np.testing.assert_equal(seq, seq_base)

        seq_base = np.array([0, 2, 1, 3])
        mlx.epc_set_phase_steps(reg_dict, seq_base)
        seq = mlx.epc_calc_phase_steps(reg_dict)
        np.testing.assert_equal(seq, seq_base)

        # TODO Dual phase
        return

    def test_external_mod(self):
        import_file = os.path.join("..", "epc660.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)

        external = mlx.epc_calc_external_mod(reg_dict)
        self.assertFalse(external)

        mlx.epc_set_external_mod(reg_dict, True)
        external = mlx.epc_calc_external_mod(reg_dict)
        self.assertTrue(external)
        # Verify we can calculate fmod and int_times
        #
        demod = 80.0
        mclk = 96.0

        fmod = mlx.epc_calc_mod_freq(reg_dict, mclk, demod)
        self.assertEqual(fmod, demod/4.0)

        int_time = mlx.epc_calc_int_times(reg_dict, mclk, demod)
        # TODO : Verify int_time is calculated correctly
        return


class MLX75026ConfigTest(unittest.TestCase):
    def test_delay_times(self):
        import_file = os.path.join("..", "mlx75026.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)

        mlx75027 = False
        delay_time = mlx.calc_analog_delay(reg_dict)
        self.assertEqual(delay_time, 0)

        fmods = [34.0, 50.0, 80.0, 100.0]
        for fmod in fmods:
            period = 1.0 / fmod
            mlx.set_mod_freq(reg_dict, fmod)

            delays = [1.0, 1.5, 2.0, 4.0, 8.0, 10.0, 16.0]
            for delay in delays:
                delay_us = period / delay
                mlx.set_analog_delay(reg_dict, delay_us)

                delay_actual = mlx.calc_analog_delay(reg_dict)
                self.assertAlmostEqual(delay_actual, delay_us, places=4)
        return


class MLX75027ConfigTest(unittest.TestCase):

    def import_export(self, import_file, export_file):
        if os.path.isfile(export_file):
            os.remove(export_file)

        self.assertTrue(os.path.isfile(import_file))

        reg_dict = mlx.csv_import(import_file)

        mlx.csv_export(export_file, reg_dict)
        self.assertTrue(os.path.isfile(export_file))
        reg_export = mlx.csv_import(export_file)

        for n in reg_dict.keys():
            self.assertEqual(reg_dict[n][2], reg_export[n][2])
        os.remove(export_file)

    def test_import_export(self):
        """
        Test the import and export functions of the CSV files 

        """
        import_file = os.path.join("..", "mlx75027.csv")
        export_file = "mlx75027_export.csv"

        self.import_export(import_file, export_file)

        import_file = os.path.join("..", "mlx75026.csv")
        export_file = "mlx75026_export.csv"
        self.import_export(import_file, export_file)
        return

    def test_nlanes(self):
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))

        reg_dict = mlx.csv_import(import_file)

        nlanes = mlx.calc_nlanes(reg_dict)
        self.assertEqual(nlanes, 4)

        mlx.set_nlanes(reg_dict, 2)
        self.assertEqual(reg_dict["DATA_LANE_CONFIG"][2], 0)
        self.assertEqual(mlx.calc_nlanes(reg_dict), 2)
        return

    def test_output_mode(self):
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)

        output_mode = mlx.calc_output_mode(reg_dict)
        self.assertEqual(output_mode, 0)
        mlx.set_output_mode(reg_dict, 4)
        self.assertEqual(mlx.calc_output_mode(reg_dict), 4)
        self.assertEqual(reg_dict["OUTPUT_MODE"][2], 4)

        with self.assertRaises(RuntimeError):
            mlx.set_output_mode(reg_dict, 5)
        return

    def test_hmax(self):
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        mlx75027 = True
        nlanes = 4
        output_mode = 0

        speeds = [300, 600, 704, 800, 960]
        hmax_expected = [0x0860, 0x0444, 0x03A8, 0x033A, 0x02B6]

        mlx.set_output_mode(reg_dict, output_mode)
        mlx.set_nlanes(reg_dict, nlanes)

        for speed in zip(speeds, hmax_expected):
            hmax = mlx.calc_hmax(reg_dict, mlx75027, speed=speed[0])
            # Verify correct calculation
            self.assertEqual(hmax, speed[1])
            mlx.set_hmax(reg_dict, hmax)

        # Now set the lanes
        nlanes = 2
        mlx.set_nlanes(reg_dict, nlanes)
        hmax_expected = [0x0E60, 0x0744, 0x0636, 0x057A, 0x0514]
        for speed in zip(speeds, hmax_expected):
            hmax = mlx.calc_hmax(reg_dict, mlx75027, speed=speed[0])
            # Verify correct calculation
            self.assertEqual(hmax, speed[1])

        # Now set the data
        output_mode = 4
        mlx.set_output_mode(reg_dict, output_mode)
        hmax_expected = [0x1CC0, 0x0E88, 0x0C6C, 0x0AF4, 0x0A28]
        for speed in zip(speeds, hmax_expected):
            hmax = mlx.calc_hmax(reg_dict, mlx75027, speed=speed[0])
            # Verify correct calculation
            self.assertEqual(hmax, speed[1])

        nlanes = 4
        mlx.set_nlanes(reg_dict, nlanes)
        hmax_expected = [0x0E60, 0x0744, 0x0636, 0x057A, 0x0514]
        for speed in zip(speeds, hmax_expected):
            hmax = mlx.calc_hmax(reg_dict, mlx75027, speed=speed[0])
            # Verify correct calculation
            self.assertEqual(hmax, speed[1])

        return

    def test_timing(self):
        """
        Test the timing calculations. Making sure we have done things correctly. 

        Also need to verify the timing calculations if preheat is used or not. 

        """

        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        mlx75027 = True

        pretime = mlx.calc_pretime(reg_dict, mlx75027)

        # Set some preheat on
        preheat = np.zeros(8, dtype=np.bool)
        preheat[0] = True
        mlx.set_preheat(reg_dict, preheat)

        mlx.set_pretime(reg_dict, pretime, mlx75027)
        pretime1 = mlx.calc_pretime(reg_dict, mlx75027)
        self.assertEqual(pretime, pretime1)
        return

    def test_roi(self):
        """
        Test the region of interest 
        """
        import_file = os.path.join("..", "mlx75027.csv")
        mlx75027 = True
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)

        row_end = 480
        col_end = 640
        row_offset = 1
        col_offset = 1
        mlx.set_roi(reg_dict, col_offset, col_end,
                    row_offset, row_end, mlx75027)

        cs, ce, rs, re = mlx.calc_roi(reg_dict)
        self.assertEqual(row_offset, rs)
        self.assertEqual(col_offset, cs)
        self.assertEqual(row_end, re)
        self.assertEqual(col_end, ce)

        row_offset = 0
        with self.assertRaises(RuntimeError):
            mlx.set_roi(reg_dict, col_offset, col_end,
                        row_offset, row_end, mlx75027)

        row_offset = 51
        row_end = 240
        col_offset = 50
        col_end = 150
        mlx.set_roi(reg_dict, col_offset, col_end,
                    row_offset, row_end, mlx75027)
        cs, ce, rs, re = mlx.calc_roi(reg_dict)
        self.assertEqual(row_offset, rs)
        self.assertEqual(col_offset, cs)
        self.assertEqual(row_end, re)
        self.assertEqual(col_end, ce)
        return

    def test_mod_freq(self):
        """
        Test the setting of the modulation frequency and the under lying registers 
        """
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)

        mod_freqs = np.arange(4, 101, 1)
        for freq in mod_freqs:
            mlx.set_mod_freq(reg_dict, freq)
            actual_freq = mlx.calc_mod_freq(reg_dict)
            self.assertEqual(freq, actual_freq)
            # XXX : TODO check underlying registers

        with self.assertRaises(RuntimeError):
            mlx.set_mod_freq(reg_dict, 3)
            mlx.set_mod_freq(reg_dict, 101)
        return

    def test_duty_cycle(self):
        """
        """
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        mod_freq = 70
        mlx.set_mod_freq(reg_dict, mod_freq)
        duty_cycles = np.arange(0.1, 1.0, 0.1)
        for duty in duty_cycles:
            mlx.set_duty_cycle(reg_dict, duty)
            actual_duty = mlx.calc_duty_cycle(reg_dict)
            # There will be some error
            self.assertAlmostEqual(duty, actual_duty, 1)
            # XXX : TODO check underlying registers
        return

    def test_binning(self):
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))
        reg_dict = mlx.csv_import(import_file)
        binning = mlx.calc_binning(reg_dict)
        self.assertEqual(binning, 0)
        with self.assertRaises(RuntimeError):
            mlx.set_binning(reg_dict, 4)

        mlx.set_binning(reg_dict, 2)
        self.assertEqual(mlx.calc_binning(reg_dict), 2)
        self.assertEqual(reg_dict["BINNING_MODE"][2], 2)
        return

    def test_leden(self):
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))

        reg_dict = mlx.csv_import(import_file)

        leden = mlx.calc_leden(reg_dict)
        leden_expected = np.zeros(8, dtype=np.bool)
        np.testing.assert_equal(leden, leden_expected)

        leden[3] = True
        leden_expected[3] = True
        mlx.set_leden(reg_dict, leden)
        self.assertTrue(reg_dict["Px_LEDEN"][2], 0x08)
        leden = mlx.calc_leden(reg_dict)
        np.testing.assert_equal(leden, leden_expected)

        preheat = mlx.calc_preheat(reg_dict)
        preheat_expected = np.zeros(8, dtype=np.bool)
        np.testing.assert_equal(preheat, preheat_expected)

        preheat[1] = True
        preheat[4] = True
        mlx.set_preheat(reg_dict, preheat)
        self.assertEqual(reg_dict["Px_PREHEAT"][2], 0x12)
        preheat_expected = mlx.calc_preheat(reg_dict)
        np.testing.assert_equal(preheat, preheat_expected)

        premix = mlx.calc_premix(reg_dict)
        premix_expected = np.zeros(8, dtype=np.bool)
        np.testing.assert_equal(premix, premix_expected)

        premix[0] = True
        premix[7] = True
        mlx.set_premix(reg_dict, premix)
        self.assertEqual(reg_dict["Px_PREMIX"][2], 0x81)
        premix_expected = mlx.calc_premix(reg_dict)
        np.testing.assert_equal(premix, premix_expected)

        return

    def test_2lanes_AB_mode(self):
        """ Make sure v0.9 of the datasheet has fixed the Mipi lane configurations """
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))

        reg_dict = mlx.csv_import(import_file)

        nlanes = 2
        mode = 4
        mipi_speed = 300

        mlx.set_nlanes(reg_dict, nlanes)
        mlx.set_output_mode(reg_dict, mode)
        hmax = mlx.calc_hmax(reg_dict, True, speed=mipi_speed)
        mlx.set_hmax(reg_dict, hmax)
        # Now export the register values.
        mlx.check_reg_dict(reg_dict)

        reg_dict["OUTPUT_MODE"][2] = 8
        with self.assertRaises(ValueError):
            mlx.check_reg_dict(reg_dict)

    def test_default_values(self):
        """
        Test the default values are calculated correctly 
        """
        import_file = os.path.join("..", "mlx75027.csv")
        self.assertTrue(os.path.isfile(import_file))

        reg_dict = mlx.csv_import(import_file)
        mod_freq = mlx.calc_mod_freq(reg_dict)
        self.assertEqual(mod_freq, 80.0)
        duty_cycle = mlx.calc_duty_cycle(reg_dict)
        self.assertEqual(duty_cycle, 0.5)
        nraw = mlx.calc_nraw(reg_dict)
        self.assertEqual(nraw, 4)
        int_times = mlx.calc_int_times(reg_dict)
        self.assertEqual(int_times[0], 1000)

        phase_steps = mlx.calc_phase_shifts(reg_dict)
        expected_steps = np.array([0.0, 0.5, 0.25, 0.75, 0.0, 0.0, 0.0, 0.0])
        np.testing.assert_equal(phase_steps, expected_steps)

        col_start, col_end, row_start, row_end = mlx.calc_roi(reg_dict)
        self.assertEqual(col_start, 1)
        self.assertEqual(row_start, 1)
        self.assertEqual(col_end, 640)
        self.assertEqual(row_end, 480)

        binning = mlx.calc_binning(reg_dict)
        self.assertEqual(binning, 0)

        return


if __name__ == "__main__":
    unittest.main()
