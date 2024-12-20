# Wiki-Gendersort

This is the code and database behind the paper [Wiki-Gendersort: Automatic gender detection using first names in Wikipedia](https://osf.io/preprints/socarxiv/ezw7p/).

The gender association to the 694 376 names is available in the file [NamesOut.txt](https://github.com/nicolasberube/Wiki-Gendersort/blob/master/NamesOut.txt) as a tab separated flat file. The categories are M (male), F (female), UNI (unisex), UNK (unknown) and INI (initials).

However, this file is best used when applied on the name tokens generated by the function ```nameclean()``` instead of the first name string directly. If the path to this git repository is in your Python path file (which you can do by running [setup.py](https://github.com/nicolasberube/Wiki-Gendersort/blob/master/setup.py) once), you can use the ```wiki_gendersort``` class to assign a gender based on the built dataset.

You can use the class ```assign()``` function to directly assign a gender on a first name's string, or the ```file_assign()``` function to assign a gender on a file of first names, separated by line breaks (\n).

```
from Wiki_Gendersort import wiki_gendersort

WG = wiki_gendersort()
WG.assign('Nicolas')
WG.file_assign('first_names.txt')
```

If your name is not in the [NamesOut.txt](https://github.com/nicolasberube/Wiki-Gendersort/blob/master/NamesOut.txt) file, you can use ```name_to_gender()``` to assign a gender based on a wikipedia search (which is how the gender in [NamesOut.txt](https://github.com/nicolasberube/Wiki-Gendersort/blob/master/NamesOut.txt) were attributed). You can also build your own NamesOut.txt database of names with ```build_dataset()```.

# Dependancies

The code uses on the following packages:
- unidecode=1.1.1
- wikipedia=1.4.0
