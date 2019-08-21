Sink dxf website the granite industy uses nationwide.  Online since May 31st, 2019:  www.silicatewastes.com

I had an old low effort website that I cobbled together with cgi bash scripting but I never really knew bash scripting and I always felt like it was a mess.  It listed sink dxf files for download.  The templaters where I work used it to see if they had to lug a sink back to the shop to draw it in CAD or if we already had a drawing.  Eventually the granite industry started using it nationwide and some people sent me more drawings.  It climbed to the top of google's listings.  I kicked around the idea of making it so people could log in and rate drawings but I didn't know how until I learned Python/Flask in Launchcode's LC101.  I had to figure out how to set up a LAMP stack and all that on my own, though.

So then I made this website.  Now instead of crossing your fingers and hoping you don't lose a few hundread dollars due to a bad drawing maybe someone else already tried it and rated the drawing good or bad.  I've got over 200 registered users since May 31st, 2019.  This new site doesn't show up much on google yet but we'll see.

I didn't use Bootstrap so I learned a lot about css.  I think if I made another project like this my css might be less of a mess and if I made a 3rd one my css might actually be good.  I did the css codeacademy stuff and I thought it was easy but then it turned out I coudn't do it.  There was new stuff I didn't learn about like flex.  I kept forgetting the difference between display and position.  I didn't know the difference between inline or inline-block.  Countless times I would try 10 different things to move something on the screen and nothing would have any effect.  Gradually I learned that the block you're working on depends on how the previous block is defined; like if you want to float: left then the previous block has to be float.  By the time I started to get the hang of it my css was already twice as long as it should have been due to me micromanaging each new block instead of having a big clear picture of how to do the whole layout.  Each element in my css is fighting against against every other element instead of working together as a whole.  So by the time I figured that out I just kept doing it the wrong way instead of starting over.

My Python code would be a little different if I did it again.  I think the biggest problem is I didn't separate each approute into 2 separate blocks for GET and POST.  I remember wondering that when I started and I decided there was some stuff I wanted to do if it was either GET or POST but in the end it just made a mess and I ended up checking the same stuff over and over.  Now that I learned java/spring I see that in there I don't think you even have the option of handling GET and POST in the same approute so it makes it kind of plain that they should be completely separated.
