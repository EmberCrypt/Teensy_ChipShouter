#include "Teensy_Cs.h"


char log_buf[0x1000];



Teensy_Cs::Teensy_Cs(int trig_out, Cs_Target *target){
	pinMode(trig_out, OUTPUT);
	digitalWriteFast(trig_out, LOW);
	this->trig_out = trig_out;
	this->target = target;
}


void Teensy_Cs::set_trig_in(int trig_in, bool trig_in_level, unsigned long trig_in_delay_muS){
	this->trig_in = trig_in;
	this->trig_in_level = trig_in_level;
	this->trig_in_delay_muS = trig_in_delay_muS;
	pinMode(trig_in, INPUT);

	this->tr_in = 1;
}

int Teensy_Cs::trigger(){
	unsigned int delayMus = (unsigned int) (this->delayNs / 1000);
	unsigned long time = micros();
	// If trig_in pin is set, wait for this pin to go to the required level
	if(this->tr_in){
		// If we have an analog trigger_in pin
		if(this->tr_in == 2){
			/*
			int flag = 0;
			while(1){
				sprintf(log_buf, "Analog read %d, ref analog read: %d", this->adc.analogRead(this->trig_in), this->analog_trig_value);
				log(log_buf, strlen(log_buf));
				if(this->adc.analogRead(this->trig_in) < 220)
					flag = 1;
				if(flag && this->adc.analogRead(this->trig_in) == 255)
					return ERR_MCU_TRIG_IN;
			}
			*/
			while(this->adc.analogRead(this->trig_in) > 208); // Wait for trigger to reset - TODO not sure if problem with other trigger setups + can lead to infinite loop
			while(this->adc.analogRead(this->trig_in) < this->analog_trig_value){
				//sprintf(log_buf, "Analog read %d, ref analog read: %d", this->adc.analogRead(this->trig_in), this->analog_trig_value);
				//log(log_buf, strlen(log_buf));
				if(micros() > time + this->trig_in_delay_muS)
					return ERR_MCU_TRIG_IN;
			}

		}
		else if(this->tr_in == 1){
			while(digitalReadFast(this->trig_in) == this->trig_in_level); // Wait for trigger to reset - TODO not sure if problem with other trigger setups
			while(digitalReadFast(this->trig_in) != this->trig_in_level){
				if(micros() > time + this->trig_in_delay_muS)
					return ERR_MCU_TRIG_IN;
			}
		}
	}
	sprintf(log_buf, "Triggering %d", this->trig_out);
	log(log_buf, strlen(log_buf));
	delayMicroseconds(delayMus);
	DELAY(this->delayNs % 1000);
	if(trig_out_pulse == 1){
		digitalWriteFast(this->trig_out, HIGH);
		DELAY(this->widthNs);
		digitalWriteFast(this->trig_out, LOW);
	}
	else{
		digitalWriteFast(this->trig_out, LOW);
		DELAY(this->widthNs);
		digitalWriteFast(this->trig_out, HIGH);
	}
	return 0;
}

int Teensy_Cs::run_target(bool trigger, uint8_t* out, uint16_t* out_len){
	int res;
	res = this->target->pre_glitch(out, out_len);
	if(res != 0)
		return res;
	if(trigger)
		res = this->trigger();
	if(res != 0)
		return res;
	res = this->target->post_glitch(out, out_len);
	return res;
}


void Teensy_Cs::run(){
	uint16_t ret_len = 0;
	int ret = 0;
	int cmd = 0;
	char in[0x100] = {0};
	uint8_t ret_data[0x2000] = {0};
	this->target->setup();
	while(1){
		while(!Serial);
		cmd = Serial.read();
		if(cmd != -1){
			ret_len = 0;
			memset(ret_data, 0, 0x20);
			switch(cmd){
				case CMD_SET_WIDTH:
					Serial.readBytes(in, 4); // New width sent in little endian order
					this->set_widthNs(*((int*) in));
					sprintf(log_buf, "Setting width %d", this->widthNs);
					log(log_buf, strlen(log_buf));
					break;
				case CMD_SET_DELAY:
					Serial.readBytes(in, 4); // New width sent in little endian order
					this->set_delayNs(*((int*) in));
					sprintf(log_buf, "Setting delay %d", this->delayNs);
					log(log_buf, strlen(log_buf));
					break;
				case CMD_RUN:
					ret = this->run_target(0, ret_data, &ret_len);
					break;
				case CMD_CHECK:
					this->target->check(ret_data, &ret_len);
					break;
				case CMD_RUN_TRIG:
					ret = this->run_target(1, ret_data, &ret_len);
					break;
				case CMD_STOP:
					return;
				case CMD_PREPARE_MCU:
					ret = this->target->prepare_target();
					break;
				default:
					sprintf(log_buf, "[%02X] unknown command byte", cmd);
					log(log_buf, strlen(log_buf));
			}
			Serial.write(cmd | 0x80);
			Serial.write(ret);
			Serial.write(ret_len >> 8);
			Serial.write(ret_len & 0xff);
			for(int i = 0; i < ret_len; ++i)
				Serial.write(ret_data[i]);
		}
	}
}


void log(const char* log_str, uint16_t len){
	Serial.write(REPLY_LOG);
	Serial.write(len >> 0x8);
	Serial.write(len & 0xff);
	Serial.write(log_str, len);
	memset(log_buf, 0, len);
}

