#include <Cs_Target.h>
#include <Teensy_Cs.h>

#define RESET	10	
#define HWSERIAL	Serial1

int Cs_Target::setup(){
	HWSERIAL.begin(115200);
	HWSERIAL.setTimeout(3);
	pinMode(RESET, OUTPUT);
	return 0;
}

int Cs_Target::prepare_target(){
	return 0;
}


/*
 * This function gets executed before the glitch
 */
int Cs_Target::pre_glitch(uint8_t* ret_data, uint16_t* ret_len){
	digitalWrite(RESET, LOW);
	delayMicroseconds(5000);
	digitalWrite(RESET, HIGH);
	return 0;
}

/*
 * This function executes immediately after the glitch
 */
int Cs_Target::post_glitch(uint8_t* ret_data, uint16_t* ret_len){
	int b = HWSERIAL.read();
	while(b!= -1)
		b = HWSERIAL.read();
	delayMicroseconds(1050);
	HWSERIAL.write(0x00);
	delay(1);
	int recv = HWSERIAL.read();
	ret_data[0] = recv;
	*ret_len = 1;
	return 0;
}


/*
 * Can be called optionally to check additional status flags, ...
 */
int Cs_Target::check(uint8_t* ret_data, uint16_t* ret_len){
	return 0;
}


/*
 * This function for providing extra functionality to the teensy
 */
int Cs_Target::process_cmd(int cmd, unsigned char* buf, unsigned short* ret_len){
	return 0;
}
