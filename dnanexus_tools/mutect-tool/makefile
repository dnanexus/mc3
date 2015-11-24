all: mutectremote mutectlocal

mutectremote:
	mkdir -p resources/opt
	wget -O resources/opt/muTect-1.1.5-bin.zip https://github.com/broadinstitute/mutect/releases/download/1.1.5/muTect-1.1.5-bin.zip
	wget -O resources/opt/picard-tools-1.122.zip https://github.com/broadinstitute/picard/releases/download/1.122/picard-tools-1.122.zip
	cd resources/opt; unzip muTect-1.1.5-bin.zip
	cd resources/opt; unzip picard-tools-1.122.zip
	cd resources/opt; ln -s picard-tools-1.122 picard
	cd resources/opt; mv picard/CreateSequenceDictionary.jar .; rm picard/*; mv CreateSequenceDictionary.jar picard
	rm resources/opt/muTect-1.1.5-bin.zip
	rm resources/opt/picard-tools-1.122.zip

mutectlocal:
	mkdir -p resources/opt/bin
	cp ../../tools/mutect-tool/mutect.py resources/opt/bin/

clean:
	rm resources/opt/bin/mutect.py
	rm -r resources/opt/*
