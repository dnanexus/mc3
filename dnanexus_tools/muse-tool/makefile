all: museremote muselocal

museremote: resources/opt/bin/MuSEv0.9.9.5 resources/opt/bin/MuSEv1.0rc
	wget -O resources/opt/bin/MuSEv0.9.9.5 http://bioinformatics.mdanderson.org/Software/MuSE/MuSEv0.9.9.5
	wget -O resources/opt/bin/MuSEv1.0rc http://bioinformatics.mdanderson.org/Software/MuSE/MuSEv1.0rc_submission_b391201
	chmod +x resources/opt/bin/MuSE*

muselocal: resources/opt/bin/muse.py resources/opt/bin/vcf_reformat.py
	cp ../../tools/muse-tool/muse.py resources/opt/bin/
	cp ../../tools/muse-tool/vcf_reformat.py resources/opt/bin

clean:
	rm resources/opt/bin/MuSE*
	rm resources/opt/bin/muse.py
	rm resources/opt/bin/vcf_reformat.py
