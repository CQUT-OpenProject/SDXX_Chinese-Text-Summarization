\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{sdxxpaper}[2026/10/31 Deep learning course paper]
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{cqutreport}}
\ProcessOptions\relax
\LoadClass{cqutreport}

\RequirePackage[a4paper,left=25mm,right=25mm,top=20mm,bottom=20mm,headheight=14pt,headsep=8mm]{geometry}
\RequirePackage{fancyhdr}
\RequirePackage{amsmath,amssymb}
\RequirePackage{booktabs}
\RequirePackage{array,tabularx,needspace}
\RequirePackage{hyperref}
\hypersetup{hidelinks,unicode=true}

\def\paper@title{}
\def\paper@college{计算机科学与工程学院}
\def\paper@major{}
\def\paper@class{}
\def\paper@author{}
\def\paper@studentid{}
\def\paper@year{}
\def\paper@month{}
\newcommand{\papertitle}[1]{\def\paper@title{#1}}
\newcommand{\college}[1]{\def\paper@college{#1}}
\newcommand{\major}[1]{\def\paper@major{#1}}
\newcommand{\classnumber}[1]{\def\paper@class{#1}}
\newcommand{\authorname}[1]{\def\paper@author{#1}}
\newcommand{\makepaperauthor}{\ifx\paper@author\@empty 姓名：\underline{\hspace{4em}}\else\paper@author\fi}
\newcommand{\studentid}[1]{\def\paper@studentid{#1}}
\newcommand{\reportyear}[1]{\def\paper@year{#1}}
\newcommand{\reportmonth}[1]{\def\paper@month{#1}}

\fancypagestyle{paperstyle}{%
  \fancyhf{}\renewcommand{\headrulewidth}{0pt}%
  \fancyfoot[C]{\thepage}%
}
\pagestyle{paperstyle}
\ctexset{section={format=\cqutheiti\bfseries\zihao{4},beforeskip=1.5ex,afterskip=0.8ex},
  subsection={format=\cqutheiti\bfseries\zihao{-4},beforeskip=1ex,afterskip=0.5ex}}
\newcommand{\paper@field}[2]{#1 & \underline{\makebox[245pt][c]{#2}}\\[1.3em]}
\newcommand{\makecover}{%
  \hypersetup{pageanchor=false}%
  \thispagestyle{empty}
  \begin{center}
    \vspace*{0.4cm}
    \includegraphics[width=11.2cm]{assets/cqut-logo-horizontal.png}\par
    \vspace{2cm}
    {\cqutsongti\bfseries\zihao{2}《深度学习》课程论文\par}
    \vspace{3cm}
    {\cqutsongti\zihao{4}
      \begin{tabular}{r@{\hspace{0.6em}}l}
        \paper@field{题\quad 目}{\parbox{245pt}{\centering\paper@title}}
        \paper@field{学\quad 院}{\paper@college}
        \paper@field{专\quad 业}{\paper@major}
        \paper@field{班\quad 级}{\paper@class}
        \paper@field{姓\quad 名}{\paper@author}
        \paper@field{学\quad 号}{\paper@studentid}
      \end{tabular}\par
      \vspace{1.3cm}
      时\quad 间\quad \underline{\makebox[4em][c]{\paper@year}} 年\quad
      \underline{\makebox[2.5em][c]{\paper@month}} 月\par
    }
  \end{center}
  \clearpage
  \setcounter{page}{1}%
  \hypersetup{pageanchor=true}%
}
\newcommand{\makepaperheading}{%
  \begin{center}{\cqutheiti\bfseries\zihao{3}\paper@title\par}\end{center}
  \vspace{0.5em}
}
\newcommand{\paperabstract}[1]{\noindent\textbf{摘要：}#1\par}
\newcommand{\paperkeywords}[1]{\noindent\textbf{关键词：}#1\par\vspace{0.8em}}
\endinput
