/*
	teensy_cw.h - library for triggering the ChipShouter from a teensy
	Created by Jan Van den Herrewegen, June 10th 2021.  
*/

#ifndef __TEENSY_CHIPW_H
#define __TEENSY_CHIPW_H

#include <Arduino.h>
#include <Cs_Target.h>
#include <ADC.h>

#define A0	14

// Define the delay between clk pulses - approximated
#define DELAY(ns) for (uint32_t i=0; i < (uint32_t) ns/4; ++i) __asm__("nop\n\t")


/*
 * Simple state machine to control the teensy from a python script 
 */
#define CMD_SET_WIDTH	0x01
#define CMD_SET_DELAY	0x02
#define CMD_RUN		0x11
#define CMD_STOP	0x12
#define CMD_RUN_TRIG	0x13
#define CMD_PREPARE_MCU		0x14
#define CMD_CHECK	0x15


#define ERR_MCU_TRIG_IN		0x80


#define	REPLY_LOG	0xa5


void log(const char* log_str, uint16_t len);

class Teensy_Cs
{
	public:
		Teensy_Cs(int trig_out, Cs_Target *target);
		int trigger();
		void set_delayNs(int delayNs){ this->delayNs = delayNs; }
		void set_widthNs(int widthNs){ this->widthNs = widthNs; }
		void set_trig_in(int trig_in, bool trig_in_level, unsigned long trig_in_delay_muS);

		void set_trig_out_lvl(bool trig_out){
			this->trig_out_pulse = trig_out;
			if(trig_out == 0)
				digitalWriteFast(this->trig_out, HIGH);	
		};

		void run();	/* Runs the teensy cs, controlled by python script on the host computer */
		int run_target(bool trigger, uint8_t* out, uint16_t* ret_len);	/* Goes through one iteration of target glitch */

		/*
		 * Analog trigger in Volt - careful! Automatically sets trigger_in pin to A0 - Pin 14
		 */
		void set_analog_trigger(float analog_trig_voltage, unsigned long trig_in_delay_muS){
			this->tr_in = 2;
			this->analog_trig_value = analog_trig_voltage / 3.3 * 255;
			this->trig_in = A0;
			pinMode(A0, INPUT);
			this->adc.adc0->setAveraging(1); // set number of averages
			this->adc.adc0->setResolution(8); // set bits of resolution
			//this->adc.setConversionSpeed(ADC_CONVERSION_SPEED::ADC_HIGH_SPEED); // change the conversion speed
			//this->adc.setSamplingSpeed(ADC_SAMPLING_SPEED::ADC_VERY_HIGH_SPEED); // change the sampling speed
			this->trig_in_delay_muS = trig_in_delay_muS;

		}

	private:
		Cs_Target *target;

		int trig_out;
		int delayNs;
		int widthNs;
		int trig_in = 0; /* Possible trigger in to wait for */

		ADC adc;

		/* For analog trigger */
		bool analog_trigger = 0;
		int analog_trig_value = 0;

		unsigned long trig_in_delay_muS = 0; /* Time to wait until trigger in goes high */
		bool trig_in_level = 0; /* Level of the input trigger to wait for */

		/* if 1: pulse goes 0->1, if 0: pulse goes 1->0 */
		bool trig_out_pulse = 1;

		int tr_in = 0;
};




#endif
