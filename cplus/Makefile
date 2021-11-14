# set pkg-config manually in different machine if needed
# [WARNING] static compilations will face linking errors

common_sources= structures.cpp utility.cpp jsmn.c
worker_sources= worker.cpp structures.cpp utility.cpp comms.cpp algorithm.cpp mongo.cpp jsmn.c
pkg-mongo= -I/usr/local/include/libmongoc-1.0 -I/usr/local/include/libbson-1.0 -L/usr/local/lib -lmongoc-1.0 -lbson-1.0
pkg-static-mongo = -DMONGOC_STATIC -DBSON_STATIC -I/usr/local/include/libmongoc-1.0 -I/usr/local/include/libbson-1.0 -L/usr/local/lib -lmongoc-static-1.0 -lsasl2 -lssl -lcrypto -lrt -lresolv -pthread -lbson-static-1.0 /usr/lib/x86_64-linux-gnu/librt.a -pthread

worker: $(worker_sources) Makefile
	gcc -o build/worker $(worker_sources) $(pkg-mongo) -fpermissive -DWORKER_MAIN -DMAKE_MAKE

fast-worker: $(worker_sources) Makefile
	gcc -o build/fworker $(worker_sources) $(pkg-mongo) -fpermissive -DWORKER_MAIN -DMAKE_MAKE -O3 -DOPTIMIZED

algt: algorithm.cpp $(common_sources) Makefile
	gcc -o build/algt algorithm.cpp $(common_sources) -DALG_MAIN -DMAKE_MAKE

optimize-speed-run: algorithm.cpp $(common_sources) Makefile
	gcc -o build/opzrun algorithm.cpp $(common_sources) -DALG_MAIN -DMAKE_MAKE -O3

stt: $(common_sources) Makefile
	gcc -o build/stt $(common_sources) -DSTRUCT_MAIN -DMAKE_MAKE

mongot: mongo.cpp $(common_sources) Makefile
	gcc -o build/mongot mongo.cpp $(common_sources) $(pkg-mongo) -fpermissive -DMONGO_MAIN -DMAKE_MAKE -DDEBUG_MONGO

smongot: mongo.cpp $(common_sources) Makefile
	gcc -o build/smongot mongo.cpp $(common_sources) -static $(pkg-static-mongo) -fpermissive -DMONGO_MAIN -DMAKE_MAKE

commst: comms.cpp $(common_sources) Makefile
	gcc -o build/commst comms.cpp $(common_sources) -DCOMMS_MAIN -DMAKE_MAKE

test: test.cpp Makefile
	gcc -o build/test test.cpp $(common_sources) mongo.cpp $(pkg-mongo) -fpermissive -DMAKE_MAKE

clean:
	rm -rf build/*