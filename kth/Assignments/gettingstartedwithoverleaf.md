Getting started with Overleaf
Getting started with the template 
Log in to Overleaf "via "Log in through your institution" using your KTH account via www.overleaf.com
From the Overleaf Project management page:

Copy the template with the new cover from https://www.overleaf.com/read/qxvttmmqbgdtLinks to an external site.  following the instructions at https://www.overleaf.com/learn/how-to/Copying_a_projectLinks to an external site. 

or

Upload a ZIP file of a project - see https://www.overleaf.com/learn/how-to/Uploading_a_projectLinks to an external site. 

rename the project (hover  near the title [in white on black at the top of the window]and then click on the pencil) - it is a good idea to include your name in the project's name - so that your supervisor(s) and examiner can easily find it in their list of project
Invite your supervisor(s) and examiner to the project by the "Inviting named collaborators" - as described at https://www.overleaf.com/learn/how-to/Sharing_a_projectLinks to an external site. 
In the file "examplethesis.tex" set the default language by passing either english or swedish  as an option to the documentclass:
\documentclass[english, bibtex]{kththesis}
%\documentclass[swedish, biblatex]{kththesis}

Note that the name of the language must be in all lower case. There are also additional options for the documentclass, such as your choice of engine to process your BibTeX data (enter "bibtex" or "biblatex").
Now fill in the title and subtitle (and later add the alternate title and subtitle) of the thesis):
%% Information for inside title page
\title{This is the title in the language of the thesis}
\subtitle{A subtitle in the language of the thesis}

% give the alternative title - i.e., if the thesis is in English, then give a Swedish title
\alttitle{Detta är den svenska översättningen av titeln}
\altsubtitle{Detta är den svenska översättningen av undertiteln}
% alternative, if the thesis is in Swedish, then give an English title
%\alttitle{This is the English translation of the title}
%\altsubtitle{This is the English translation of the subtitle}
In the file "custom_configuration.tex", fill in the (missing) information about the author(s) of the thesis, the supervisor(s), and the examiner. Fill in the information about your program, the degree that you intend to apply for, the course code, etc. If you are doing your degree project outside of KTH, then fill in the information about the host organization.
Note that if you have been given a ZIP file, much of this information may already be filled in for you.
Configure the LaTeX engine using the Overleaf "Menu" pulldown - see instructions at https://www.overleaf.com/learn/how-to/Changing_compilerLinks to an external site. 
The template should work with pdflatex, XeLaTeX, and LuaLaTeX. If you are using Overleaf, I strongly recommend using XeLaTeX — as this will get the Arial fonts correct for the KTH cover. If you are running the compiler on your local machine and you use XeLaTeX and you have Arial as a system font, then it will be able to use it. Similarly, for LuaLaTeX. For pdflatex I have used \fontfamilyhelvet, i.e., Helvetica, as it is a sans serif font.
Make sure the "Main document" is set to "examplethesis.tex"
Click on the Recompile button to see your changes. Note that if you have another ".tex" file selected in the list of files on the left, Overleaf will try to compile this document and since it is likely missing a "\begin{document} you will get a large number of errors. Simply highlight the "examplethesis.tex" file in the list of files and click "Recompile".
If you logged in via your KTH account, you can also turn on "Track changes" - see https://www.overleaf.com/learn/how-to/Track_Changes_in_OverleafLinks to an external site. 
See the file "README_author.tex" for more information about the template and how to get started with your writing.
Continue editing your thesis
This new version of the template includes extensive documentation for authors, examiners, and DiVA administrators in the appendix. Feel free to delete material that is not relevant to you. The easiest way to avoid the unwanted material is to go toward the bottom of the "examplethesis.tex" file and comment out or delete the lines that does an include of the irrelevant file (and of course remove the unnecessary "\cleardoublepage" commands):

% Information for authors
\include{README_author}

\cleardoublepage
% information about the template for everyone
\include{README_notes/README_notes}

\cleardoublepage
% information for examiners
\include{README_notes/README_examiner_notes}

\cleardoublepage
% information for administrators
\include{README_notes/README_for_administrators.tex}
Note that you should not delete the "For DIVA" page or pages, since this information will be used later by the DiVA administrators to enter the data concerning an approved thesis into DiVA. You can of course comment out the lines between "\kthbackcover" and "\end{document}" while working on your thesis, but be sure to uncomment them before you make your final version of the thesis!

You can, of course, rename the examplethesis.tex file to your choice of filename but make sure you change the "Main document" configuration via the "Menu".

Should you encounter problems with the template or have constructive feedback, please send mail to maguire@kth.se.

Best of success in your degree project!

Instructions for old template
Enter the URL https://www.overleaf.com/latex/templates/kth-thesis-template-for-1st-and-2nd-cycle-degree-projects/yrvvwpbwdzghLinks to an external site. into your browser and you will see:
First view of project in Overleaf  
Next, open as a template:
Open_as_template-Screenshot_20210203_111717-1.png    
rename the project (hover  near the title [in white on black at the top of the window]and then click on the pencil):
Rename project
New name:
New project name
Share the project by clicking the button
  Share button
  


This gives a popup:
Share popup
You can either enter the names of your examiner, supervisor, etc. into the window for "Share with your collaborators" or choose turn on link sharing and then copy the "Anyone with this link can edit this project" link and send it to your examiner, supervisor, etc.
Sharing links  
Now choose the language of the thesis:

%% set the default lanage to english or swedish by passing an option to the documentclass - this handles the inside tile page
\documentclass[english]{kththesis}
%\documentclass[swedish]{kththesis}
Now fill in the title and subtitle (and later add the alternate title and subtitle) of the thesis):

%% Information for inside title page
\title{This is the title in the language of the thesis}
\subtitle{An subtitle in the language of the thesis}

% give the alternative title - i.e., if the thesis is in English, then give a Swedish title
\alttitle{Detta är den svenska översättningen av titeln}
\altsubtitle{Detta är den svenska översättningen av undertiteln}
% alternative, if the thesis is in Swedish, then give an English title
%\alttitle{This is the English translation of the title}
%\altsubtitle{This is the English translation of the subtitle}
Fill in the information about your supervisor(s) [they are named A and B]:

\supervisorAsLastname{Supervisor}
\supervisorAsFirstname{A. Busy}
\supervisorAsEmail{sa@kth.se}
% If the supervisor is from within KTH add their KTHID, School and Department info
\supervisorAsKTHID{u100003}
\supervisorAsSchool{\schoolAcronym{EECS}}
\supervisorAsDepartment{Computer Science}
% other for a supervisor outside of KTH add their organization info
%\supervisorAsOrganization{Timbuktu University, Department of Pseudoscience}
Fill in the information about your examiner:

\examinersLastname{Maguire Jr.}
\examinersFirstname{Gerald Q.}
\examinersEmail{maguire@kth.se}
% If the examiner is from within KTH add their KTHID, School and Department info
\examinersKTHID{u100004}
\examinersSchool{\schoolAcronym{EECS}}
\examinersDepartment{Computer Science}
% other for a examiner outside of KTH add their organization info
%\examinersOrganization{Timbuktu University, Department of Pseudoscience}
Fill in the information about your host company or organization:

\hostcompany{Företaget AB} % Remove this line if the project was not done at a host company
%\hostorganization{CERN}   % if there was a host organization
Fill in your program code:

\programcode{TCOMK}
%% Alternatively, you can say \programme{Civilingenjör Datateknik} to directly set the programme string
finally - click on the recompile button to see your changes:
recompile-Screenshot_20210203_120858.png  
Continue editing your thesis