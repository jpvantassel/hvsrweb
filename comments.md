# Comments

- Overall the app looks great!
- Although its quite a bit slower the interactive plot is pretty cool. I
hope in the future we can get this working much faster to be a viable
alternative.
- The low-cut frequency box is surrounded by a red ring. Try changing
it from `int` input to `float`. You may also want to change the valid range.
- Remove the `Settings` heading from each tab, I dont think we need this
What would be nice is to put the `Settings` header above the
`Time Domain`, `Frequency Domain`, and `H/V` tabs. So that is clear
these tabs are settings for each of the categories.
- Fix the red ring around `minimum frequency after resampling` and
`number of frequencies after resampling`.
- When I view the app in half-screen mode, The drag to drop gets put at
the bottom of the page, would be nice to have this appear at the top.
- Also see if you can make the drag-and-drop window much larger so it
will essentially take up the entire right panel.
- I think we should try and shorten the names for each setting and move
the longer descriptions to scroll-over text. Think about what we should
use for shorter names, and make some changes we discuss what you come up 
with on the next revision.

I think that is it for now, great job!

## Comments 2/24/2020

- Update table results table to match those shown in current Jupyter notebook.
- Make the drag and drop fill the entire page width
- Label the section where the file name is printed to be `Uploaded File: <filename>`
- Place the three results tables next to each other in the same row with a title over each rather
than just text. We can call them Window Information, Statistics Before Rejection, and Statistics After
Rejection.
- Fix the upload data function so we can upload any file, rather than just the example file.
- Write results to json and store in hidden div.
- Implement save figure and save file.

## Comments 3/13/2020

### General Feedback

- Prefer descriptive names over comments wherever possible. For example
"tab1_content" becomes "time_tab", this way when you see "time_tab" later in the
code you will immediately recognize it without having to refer to the comment.
And if the name changes in the future you won't have to worry about updating
your comments.
- Remove unecessary imports, the fewer imports you have the less likey you are
to get an import error, it will also help speed up your code.
- `autopep8` is a really great autoformatting tool. In vscode I have it hotkeyed
to `shift+alt+f` and it does all the formatting. It sometimes does weird
things with line breaks but generally its a good timesaving tool.
- You will want to be more specific with the `Parameters` of a docstring. Then
what we have currently in main. [Here](https://github.com/jpvantassel/hvsrpy/blob/8b6e34c14e44758cebeb560a3f2334cfef3b7e2f/hvsrpy/sensor3c.py#L191)
is an example of a more specific docstring from `hvsrpy`. But dont worry about
changing any of them right now. The other docstrings you wrote we good, thanks
for doing that.

### Future Work

- Lets shoot for a tri-colored scheme of blue, white, and grey since we are
nearly there anywas. Change `calculate` to form green to blue. Side note maybe
in the future we could go for UT colors? For example like I did on our Geotech
student site [utgeoinstitute.com](https://www.utgeoinstitute.com/). What do you
think?
- Look into how we can change the favicon and page title (see file
`favicon_and_name.png` for an image of what I am talking about). There must be a
way to change this to a custom icon and name, right? For now we could use the
favicon I came up with for my website [here](https://github.com/jpvantassel/research-website/blob/master/images/geoseis.png?raw=true).
We could name the page `hvsrpy-app` for now. Ideas are very much welcome!
- Lets change how the demo button works. Rather than demo running the
calculation lets have it load the demo miniseed file into memory. This way the
user can play around with the settings and press calculate multiple times using
the demo file and get a feel for the parameters.
- We need to find a way to keep track of the file's human readable name so when
we save the .hv file we dont get a bytes.IO object hash in the output file.
- I need to come up with a new name for `save .hv`, as I dont think this is
clear enough for a new user. Putting this here as a reminder to myself.
- We need to think about a new way of formatting the tables so they fit more
naturally on the page, I feel they are a bit squished right now. Try moving
things around a bit and see what you can come up with. We'll keep tweaking
things until they feel natural. This might be a bad idea, but maybe we could
have a fourth tab open up after the calculation is complete with the results. We
could call it `Results`. Inside would be the information from the tables, though
not as a table. We would have three sections (one for each table) and one line
per section with the information from each line of the tables. We could also
move the save buttons inside that tab as well (since the user cant use them
until the calculation is run anyways). Try mocking this up and see what you
think.
- Can we shift the figure up so that its directly below the drag and drop?
Ideally we would be able to see the entire figure and legend at 100% zoom on
Chrome. This way folks dont accidentally miss that their is a legend. If
`Current File` is part of its own row, we can stick it at the top of `Settings`
in the left most column. And actually lets just the `Settings` header as I dont
think we really need it. Its fairly obvious those are settings.
