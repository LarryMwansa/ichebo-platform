# Bible Reader UI Improvements

The current positioning of elements:

## `class=bible-reader-shell`

- The body of the whole content
-

## `class=Topbar`

- This chapter navigation

### `class=bible-translation-row`

- This is bible versions list
-
- This is be a view / page with a list of versions
- It should have a link to

## `class=bible-chapter`

- Chapter content

## `class=bible-annotation-overlay`

- Bible Drawer Context
- Here it has Bible Note

Some bible note context issues:

- not scrolling on mobile view, on phone
- When you scroll with finger the chapter page is the one scrolling
- Buttons Save Note and Publish to Branch either don't have background color or have white color

## `class=sheet bible-navigator`

- has drawer for bible navigation

---

# Proposed Positioning of Elements to Improve Bible

## `class=bible-reader-shell`

- main body the house the ui

## `class=Topbar`

- let there be top bar consisting of bible context menu and link
- Bible versions button/ link that leads to Bible versions list page
- Bible Versions list page, shoud also have button/link leading to Bibles / Bible version by languages. The   `class=bible-translation-row` comes
- search button that should open search page
- bible settings button that activates context drawer that houses font settings
- the topbar should be sticky retracing when on scroll, that behaviour should also be for the bottom bar, it retract to make more reading room.

## `class=bible-chapter`

- Chapter content

## `class=sheet bible-navigator` (Proposed)

- place the chapter heading and navigation in between `class=bible-chapter` and `class=bottom bar`
- let be the activator for `class=sheet bible-navigator` drawer
- however I suggest removing the bible-navigator out the drawer into a page as suggest for bible version list.
- the chapter navigator with previous and next buttons can now become this bible-navigator button.
- Where the chapter is such actual button for the bible-navigator.
- one scroll the bottom bar can retract while the chapter heading navigator is sticky to the bottom.Trigger back to postion on scroll

## App Drawer aka Context drawer

- the app drawer evolves to context drawer to cater for the various options required that window and context
- Originally it housed apps but there is a redundancy. The bottom bar by default should house the buttons / links for app.
