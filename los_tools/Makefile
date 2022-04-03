.PHONY: zip

prepare: clean delete

zip: prepare zipfiles

clean:
	py3clean .

delete:
	find . | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf

zipfiles:
	pb_tool zip
