library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.std_logic_unsigned.all;


entity pwmmod is
	generic (
		CNT_BITS	: integer := 10
	);
	port (
		rst_i	: in std_logic;
		clk_i	: in std_logic;
		en_i	: in std_logic;
		duty_i	: in std_logic_vector(CNT_BITS - 1 downto 0);
		pwm_o	: out std_logic;
		test_int : in integer range 0 to 15;
		test_uns : out signed(7 downto 0)
	);	
end entity pwmmod;
