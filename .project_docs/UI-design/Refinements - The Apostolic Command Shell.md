
# Refinements - The Apostolic Command Shell


The Apostolic Command Shell is work in progress. Therefore it will go through various versions before we can safely says we have an existing frame of design, idea, tools and implementation. I will lead with what I feel should go into. And I will have you as my Chief design. Chief Engineer,  My Co Team Developer,  your expertise knowledge, and understanding will be used for the project. What will direct, suggest, advise, plan and execute on what conventionally happens in a project of this scale. 

---

## Stage Mode and Mobile Mode Approach

The idea now that we have web UI. WE need to further develop Stage Mode and Mobile Mode rendering of the UI. I feel that we need to have these two into a robust two-prone UI system. I feel that the mobile Mode should be fallback for user in that absence of Mobile app infrastructure. In the cases that it might be down. 

So there should be an implementation of views and templates that should handle this. So far we used some of Django's ability to handle this. I would love to explore this further and have an architecture built to handle this rigorously thought off and designed and built and works without a hitches.

### Stage Mode

Templates, views other design elements design to work in Web UI mode. Each feature and its templates should be retrofitted where possible or built anew, base on the DESIGN.MD direction . And optimise to work on desktop mode.

### Mobile Mode

Templates, views other design elements design to work in Web UI mode. Each feature and its templates should be retrofitted where possible or built anew, base on the DESIGN.MD direction . And optimise to work on mode mode. The Flutter app and Mobile Mode should bear resemblance. Stage Mode & Mobile mode should allow the UI to be PWA ready.


---
## Four-Column Grid Architecture


**On the Shell**

The architecture stills refining. I'm currently happy with how it looks. It is still raw though, and it need finesse. My observations:

- I feel that context bar (maybe not so much that context bar) and options bar will need to be allowed to be draggable to adjust their width when need be. I would suggest that it have default with set to the current width. Then if refreshed or closed and reopen it goes back to default width.
- Or it can keep the what memory of the UI adjustments. Then have a restore to default view in settings.
- I feel that we must hold on to names that mobile UI has set of app etc. I have notice several name changes for the same things. It is causes confusion. 

**Column 1: Primary Sidebar (Global Nav)**

 My observations the number of icons are currently overlapping the screen height. Two approaches how to fix this:

A. Accessibility issues with having a nav that only icons to describe the link. 
- I have observed there are tool-tip pop-ups when you hover close. 
- But i find myself having to guess which icon leads to where. 
- Maybe make it slightly wide enough to place a name next to icon

B. Scrollable Nav:
- We might have to make that nav scrollable.
- Let it have icon arrows at each end to indicate it is scrollable
- Let is have tool-tips that pop-up to indicate the nav is scrollable
- We might need to consider placing the icons according to importance and categorically

C. Organising nav items to be grouped with complementary items.
- Maybe take some icons off the nav and place them within other windows where they are complementary.
- Pairs that work:
	- Apostolic Web (Graph) can go with Governance
	- Calendar can go with Activity
D. Maybe we can have a more... option with a dropdown to the side with the rest of the icons and links. 

**Column 2: Context Bar (App Explorer)**
- all the apps actions should occupy the context bar
- Here we must find complementary apps or features
- The styling for the contextual bar should uniform across the shell
- Let's stick to buttons where applicable
- Where list is long as in the Desk handling record types let collapsible buttons with accordion type of dropdown within the bar.
- Colours especially accent colour should uniform across the shell. current the activity is spotting  pink for accent instead of the institution red.
- currently the majority of pages have icons that are not styled
- Let settle for a uniform approach on places items in the context bar to promote uniformity 

**Column 3: The Stage (Sovereign Canvas)**
- the headings all typography should. The Design.md has prescribe the hero heading and the watermark. This is institutional branding.
- Dashboard page is currently sporting white colour of all the heading other text.
- Colours especially accent colour should uniform across the shell. current the activity is spotting  pink for accent instead of the institution red.

**Column 4: Options Bar (Sidecar & Metadata)**

- The properties of the actions of that app or page should be housed in the options bar.
- where they are now action it is will be what is the most likely apps or tools that might go with that window.
- It can serve as quick access for forms related to apps that relevant to that window. For example the desk will need the bible as tool in the sidecar. in the other tab links & relationship. While in other tab it can hold forms that a small will.
- The options is tabbed window that means it can house various options, tools and apps
- To be the working area for forms in the case of a window that uses forms like the desk


---

## Command Palette / Command Mode:

There is a Focus Mode Command, but there is now command to reverse Focus Mode


---

# Observations Per App

## Dashboard / Command Centre

- I feel that this dashboard can do better in working as a status page as well as window into the relevant places. Places such as community, gathering & events etc, activity & calendars and ministry bulletins 
- Paraclete divine intel seats right after the heading of the page. On let other things follow. 
- Let's have the same gradient that mobile is using for the Divine intel applied to the one on the shell.
- The Registry Activity is a great idea but it to long
- Community card should be here 
- The cards Daily Briefing, Active Mandates, and Formation Progress  the light mode colours are similar to the background color


## The Desk 

- It is needs to go into next phase of building and improvements.
- Optimise contextual bar. 
- Rename the Registry Origin to Record Family 
- Add a collapsible options for the Record Type
- currently none of the types here are opening in the stage once clicked
- The ide is to have the records types records,  activity, governance libraries have their forms get developed in this once place. It is like the word process plus obsidian work area.
- Apps records, activity, governance libraries, and Apostolic Web (Graph) links must be here in the contextual bar
- These could be moved into options bar to acts properties. 
- The writing stage will need further developing. 
- Develop the menu/ toolbar. It should carry formatting tools, saving etc. 
- It should be similar to CK Editor does.
- It is render markdown and edit in markdown. And preview right in the writing canvas like how Obsidian has a preview or reading that also works as editing space. We can have a button to activate this mode
- position it bottom like maybe 100px above the bottom. But please advise if this good UI/UX. This is will be complemented by the right-click option menu in the body on the text.
  - the ability to highlight 

## Records & Journals

Contextual bar:
- links (icons etc ) should house in buttons like the governance app contextual bar buttons styles. 
- The Governance app contextual bar buttons are the go to style for the contextual buttons.

Stage window:
- The lists rendered in here
- a record should open in the stage window, and have a back button 
- If click edit it should lead open in the desk canvas to edit it once saved it can lead back to records, advise if this is a good approach

**Options Bar (Sidecar & Metadata)**
- The properties of the record should appear in the options bars. In case of records the record type, links and relationship information, source like author metadata
- And any other properties you might advise that I might have missed

## Governance app

Contextual bar:
- I love the button and links styling this should be the standard for contextual bar styling
- There are three reference libraries in governance, Reference, Key, Mandate libraries. They be all presented in the contextual bar. 
- Their actions should placed in the contextual bar as well  

Stage window:

- the governance record should render in the stage window. Not happening currently.

**Options Bar (Sidecar & Metadata)**

- - The properties of the record should appear in the options bars. In case of records the record type, links and relationship information, source like author metadata, versioning

## Community 

Contextual bar:

- style the buttons links using the standard governance style contextual bar styling
- it looks like that are number of pages in community. Please arrange so that each page has contextual actions that 


Stage window:

- members, pipeline, management, upcoming pages is using older version of the web ui base template. Retrofitting and place the options accordingly 


**Options Bar (Sidecar & Metadata)**

- make suggestions of the properties for each page in community

## Learn 

- follows the same issues and solutions as Community
- Fix the hero heading
- Induction review and content review are throwing errors  TemplateSyntaxError at /learn/review/ + TemplateSyntaxError at /learn/induction/review/


## Activity 

**Contextual bar:**
- colour of accent is pink and not the institutional red
- style the button according to the governance app contextual styling
- bring the standard alone calendar to activity


**Stage window:**
- colour of accent is pink and not the institutional red
- the cards is need real data
- Make sure that there is real data in the pages

**Options Bar (Sidecar & Metadata):**
- get the appropriate properties which actions


## Bible App

**Contextual bar:**
- the book chapter navigation into the conceptual bar
- bible version selector

**Stage window:**
- figure out how to implement bible notes, linking verse etc that works in mobile mode through the contextual drawer. 

**Options Bar (Sidecar & Metadata):**
- figure out what properties go here


## Live 

**Contextual bar:**
- There is no contextual actions that go with this app setup in the contextual bar
- Figure out the actions an add them

**Stage window:**
- help in organising this to be able to show the preview video window and the schedule window
- Here the operator should to add video to a timeline
- Able to see the timeline and video that is playing 
- Something with church online approach

**Options Bar (Sidecar & Metadata):**
- suggest the properties

## Tenancy Management App

**Contextual bar:**
- There is no contextual actions that go with this app setup in the contextual bar
- Figure out the actions an add them

**Stage window:**
- suggest how we can improve the content here
- 

**Options Bar (Sidecar & Metadata):**
- suggest the properties