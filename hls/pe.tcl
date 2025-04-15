solution file add ./pe.cpp
go compile
solution library add nangate-45nm_beh -- -rtlsyntool DesignCompiler -vendor Nangate -technology 045nm
go libraries
directive set -CLOCKS {
    clk {
        -CLOCK_PERIOD 1 \
        -CLOCK_EDGE rising \
        -CLOCK_HIGH_TIME 0.5 \
        -CLOCK_OFFSET 0.000000 \
        -CLOCK_UNCERTAINTY 0.0 \
        -RESET_KIND sync \
        -RESET_SYNC_NAME rst \
        -RESET_SYNC_ACTIVE high \
        -RESET_ASYNC_NAME arst_n \
        -RESET_ASYNC_ACTIVE low \
        -ENABLE_NAME {} \
        -ENABLE_ACTIVE high
    }
}
go assembly
go architect
go allocate
go extract

