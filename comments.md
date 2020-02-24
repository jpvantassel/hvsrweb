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
