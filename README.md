Sink dxf website the granite industy uses nationwide.  Online since May 31st, 2019:  www.silicatewastes.com

I had an old website that I cobbled together with cgi bash scripting but I never really knew bash scripting and I always felt like it was a mess.  It listed sink dxf files for download.  The templaters where I work used it to see if they had to bring a sink back to the shop to draw it in CAD or if we already had a drawing.  Eventually the granite industry started using it nationwide and some people sent me more drawings.  I kicked around the idea of making it so people could log in and rate drawings but I didn't know how until I learned Python/Flask in Launchcode's LC101.  I had to figure out how to set up a LAMP stack and all that on my own, though.

So then I made this website.  Now instead of crossing your fingers and hoping you don't lose a few hundred dollars due to a bad drawing maybe someone else already tried it and rated the drawing good or bad.  I've got 300 registered users since May 31st, 2019.

I suppose I need to pull the model code out and put it in a separate file from the contoller code.  Maybe I will someday.

It all runs in main.py.  Also you might want to check out yo.py.  It's a script I wrote after I mistakenly loaded 1000's of duplicate files, one file name with an underscore and the other with a space.  Many files already had ratings.  I wrote yo.py to comb all the directories and find all duplicate files and if none or just one of the files had ratings, then put all the ratings on the space version and delete the underscore version.  If they both had ratings then I left both files up.
