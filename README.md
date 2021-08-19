# SDN-Automation-with-NSO

Project Structure:

````
.
├── Yang
├── build
│   └── book.pdf
├── chapters
│   ├── 01-Intro.md
│   ├── 02-NSO_Admin.md
│   └── 03-NSO_Develop.md
├── images
└── metadata.yml
````
- Build: Generated files.
- Chapters: Sections of the book.
- Metadata: Additional info

To compile the PDF book:

````
pandoc -o build/book.pdf metadata.yml chapters/01-Intro.md chapters/02-NSO_Admin.md chapters/03-NSO_Develop.md 
--table-of-contents --number-sections
````
