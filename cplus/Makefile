# set pkg-config manually in different machine
# make sure global.h is configured correctly 

common_sources= structures.cpp utility.cpp
worker_sources= worker.cpp structures.cpp utility.cpp comms.cpp algorithm.cpp mongo.cpp
pkg-mongo= -I/usr/local/include/libmongoc-1.0 -I/usr/local/include/libbson-1.0 -L/usr/local/lib -lmongoc-1.0 -lbson-1.0

worker: $(worker_sources) Makefile
	gcc -o build/worker $(worker_sources) $(pkg-mongo) -fpermissive -DWORKER_MAIN -DMAKE_MAKE

algt: algorithm.cpp $(common_sources) Makefile
	gcc -o build/algt algorithm.cpp $(common_sources) -DALG_MAIN -DMAKE_MAKE

stt: $(common_sources) Makefile
	gcc -o build/stt $(common_sources) -DSTRUCT_MAIN -DMAKE_MAKE

mongot: mongo.cpp $(common_sources) Makefile
	gcc -o build/mongot mongo.cpp $(common_sources) $(pkg-mongo) -fpermissive -DMONGO_MAIN -DMAKE_MAKE

test: test.cpp Makefile
	gcc -o build/test test.cpp

clean:
	rm -rf build/*