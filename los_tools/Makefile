.PHONY: zip

prepare: clean delete

zip: prepare zipfiles delete_after_zip

clean:
	py3clean .

delete:
	find . | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf

zipfiles:
	pb_tool zip

delete_after_zip:
	rm -rf zip_build/los_tools
	rm zip_build/*README.txt
