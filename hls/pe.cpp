#include <ac_channel.h>
#include <ac_int.h>

typedef int data_t;

struct packet_t {
    data_t data;
    bool end_of_stream;
};

#pragma hls_design top
void pe(
    ac_channel<packet_t> &left_in,
    ac_channel<packet_t> &up_in,
    ac_channel<packet_t> &down_out,
    ac_channel<packet_t> &right_out,
    ac_channel<packet_t> &result_out
) {
    data_t acc = 0;
    bool left_eos = false;
    bool up_eos = false;
    data_t left_data = 0;
    data_t up_data = 0;
    bool left_packet_valid = false;
    bool up_packet_valid = false;

    #pragma pipeline_init_interval 1
    while (!left_eos || !up_eos) {
        if (!left_packet_valid) {
            packet_t pkt;
            left_packet_valid = left_in.nb_read(pkt);
            left_data = pkt.data;
            left_eos = pkt.end_of_stream;
        }

        if (!up_packet_valid) {
            packet_t pkt;
            up_packet_valid = up_in.nb_read(pkt);
            up_data = pkt.data;
            up_eos = pkt.end_of_stream;
        }

        if (left_packet_valid && up_packet_valid) {
            acc += left_data * up_data;
            packet_t right_packet, down_packet;
            right_packet.data = left_data;
            right_packet.end_of_stream = left_eos;
            down_packet.data = up_data;
            down_packet.end_of_stream = up_eos;
            right_out.write(right_packet);
            down_out.write(down_packet);
            left_packet_valid = false;
            up_packet_valid = false;
        }
    }

    packet_t result_packet;
    result_packet.data = acc;
    result_packet.end_of_stream = true;
    result_out.write(result_packet);
}
