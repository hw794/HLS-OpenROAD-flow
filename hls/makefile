HLS = catapult -shell -file

PE_SRC = pe.cpp
PE_TCL = pe.tcl
PE_VERILOG = Catapult/pe.v1/rtl.v

$(PE_VERILOG): $(PE_TCL) $(PE_SRC)
	$(HLS) $<

.PHONY: clean
clean:
	rm -rf Catapult
	rm -f Catapult.ccs
	rm -f catapult.log
