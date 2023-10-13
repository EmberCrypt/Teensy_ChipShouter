#ifndef __CS_TARGET_H_
#define __CS_TARGET_H_

#include <Arduino.h>

extern char log_buf[];

/*
 * TODO change funcs to work with this struct instead of int & uint8_t*
 */
typedef struct{
	int return_code;
	uint16_t len;
	uint8_t* out;
} ret_struct;

class Cs_Target
{
	public:
		Cs_Target(){};

		/*
		 * NOTE: best to give different error codes to each of these functions for other scripts to understand what went wrong
		 */

		/* Set up the target - happens once */
		virtual int setup();

		/* Runs the target up until the glitch insertion */
		virtual int pre_glitch(uint8_t* out, uint16_t* out_len);

		/* Runs the target functions after the glitch */
		virtual int post_glitch(uint8_t* out, uint16_t* out_len);

		/* Checks the result of the glitch etc */	
		virtual int check(uint8_t* out, uint16_t* out_len);

		/* Gets the MCU in the correct state before glitches are run. Can be called once after which run() is called many times */
		virtual int prepare_target();

		/*
		 * Possibility for the target class to implement a command handler as well
		 * Commands with ID from 0x20 are forwarded to this method
		 */
		virtual int process_cmd(int cmd, uint8_t* ret_data, uint16_t* ret_len);

};


#endif
