# Ftrack-Actions
 Custom actions for Ftrack. 
 
 copy-path
  - Copies file path of the latest nuke script to the clipboard.
  
 create-cis
  - Creates a Cuts-In-Sequence for all the shots within the selected sequence.
  
 create-contact-sheet
  - Createas a contact sheet from selected shots/tasks.
  
 generate-actuals
  - Creates an exel sheet that contains billing and productivity information for each shot/task.
  
 initialize
  - Update Shot Params : Updates Shot entities. 
  - Update Paths : Updates Paths of all items in the selected hiearchy. These paths connects Ftrack with the Studio folder structure.
  - Initialize Selected : Creates Files and Folders. 
  
 notes
  - Latest shot note to task : Duplicate a note on shot level to task level
  - Latest task note to all other tasks : Duplicate a note to all other tasks for a given shot
  - Shot Description as task note : Get shot description and make it a note
 
 open-output
  - action_open_output : Opens custom version of a shot
  - djvview_task2 : Launch Latest Shot/Task in DJV_View
  - djvview_task : Launch Shot/Task in DJV_View
  - open_folder : Opens the task directory
  - open_plates : Opens the plate directory


 package
  - Shot : Packages an entire shot to be used as a standalone shot in a non-studio environment. Useful for Archiving a shot and all the assets taht is being sourced by the latest nuke file. 
  - MatchMove : Packages match-move frames and the plates that are needed to be sent off to external vendors.
  - Roto : Packages roto frames and the plates that are needed to be sent off to external vendors.
 
 qc-for-nuke : Paste the copied code into nuke's QC node. This nod then imports all the QC files to be inspected in nuke.
 
 review-submission : Slates a given shot and uploads it to Ftract to be reviewed remotely. (Outdated.... use cineSync)
 
 slapcomp
  - Slap comps the 3d renders using plate and roto (if available)
  
 slate
  - Create : Creates a slate item. 
  - Modify : Modifies an existing slate. 
  - Slate : Slates the selected item(s)
  
thumbnails
  - Updates the thumbnails of selected items.
 
