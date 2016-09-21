'''
Creation of an FKIK setup system

@Author: David Major - Instructor
@Project: Class - Script Programming: CCM391A
@Company: Art Institute of Vancouver

Latest update: 2016/07/31 (YYYY/MM/DD)
    - All from scratch : based on work done in class and using better PyMEL examples
'''
import pymel.core as pm


class FKIK_setup(object):
    debugging = True
    
    # Various tool attributes #
    guide_name_list = ['shoulder_LOC', 'elbow_LOC', 'wrist_LOC']
    slave_name_list = ['slave_shoulder_JNT', 'slave_elbow_JNT', 'slave_wrist_JNT']
    FK_name_list = ['FK_shoulder_JNT', 'FK_elbow_JNT', 'FK_wrist_JNT']
    IK_name_list = ['IK_shoulder_JNT', 'IK_elbow_JNT', 'IK_wrist_JNT']
    
    base_pos_list = [[-5.0, 0.0, 2.0],
                    [0.0, 0.0, 0.0],
                    [4.0, 0.0, 2.0]]
    
    # UI Attributes #
    win_name = 'exampleUI' # Must be a 'legal' name to Maya (A-Z, 0-9, _) !!! No spaces !!!
    window_development = True # A trigger for deleting existing UI window preferences: True / False
    
    # Set up functions: UI first, related functions next.
    ## UI FUNCTION ##
    def UI(self):
        # Clean up old windows which share the name
        if pm.window(self.win_name, exists=True):
            pm.deleteUI(self.win_name)
        
        # Clean up existing window preferences
        try:
            if pm.windowPref(self.win_name, query=True, exists=True) and self.window_development:
                pm.windowPref(self.win_name, remove=True)
        except RuntimeError:
            pass
        
        # Declare the GUI window which we want to work with
        self.my_win = pm.window( self.win_name, widthHeight=[200,150] )
        base = pm.verticalLayout()
        
        with base: # Using the variable created 2 lines above, we can nest inside that layout element
            with pm.verticalLayout() as header: # We can also assign a variable while creating the layout element
                pm.text('FK/IK Setup')
                pm.separator()
            with pm.verticalLayout(): # The assignment of a variable to the layout is optional
                #pm.button( ) # This button does nothing!
                pm.button( label='Create Guides', command= self.FKIK_create_guides ) # First way to execute a command with a button
                pm.button( label='Create Joints', command= self.FKIK_create_joints_from_guides ) # First way to execute a command with a button
                #pm.button( label='Create Orient Helper', command= self.FKIK_query_guide_orient )
            
        
        # Fix spacing of layout elements
        base.redistribute(.1)
        header.redistribute(1,.1)
        
        # Last lines of code
        self.my_win.show()
        #return [my_win, base, header, btn_ID] # Debugging purposes only
        
    
    ## SUPPORTING FUNCTIONS ##
    def FKIK_query_guide_translation(self, *args):
        return [self.shoulder_guide.getTranslation(space='world'),
                self.elbow_guide.getTranslation(space='world'),
                self.wrist_guide.getTranslation(space='world')]
    
    
    def FKIK_query_guide_orient(self, *args):
        print 'Querying the rotations of the guides which were placed.'
        POS_list = self.FKIK_query_guide_translation()
        
        # TODO:
        #     Replace all this code with something a little
        #     more elegant.
        
        #     Likely something with OpenMaya for querying the
        #     actual vectors and orientations of the objects
        #     in world space?
        
        #     Using cross products to determine the correct
        #     planar relationships between guide positions.
            

        A_LOC = pm.spaceLocator()
        B_LOC = pm.spaceLocator()
        C_LOC = pm.spaceLocator()
        
        if self.debugging: print 'Created:', A_LOC, B_LOC, C_LOC
        
        A_LOC.setTranslation(POS_list[0])
        B_LOC.setTranslation(POS_list[1])
        C_LOC.setTranslation(POS_list[2])
        
        A_orient = pm.aimConstraint(B_LOC, A_LOC, aimVector=[1,0,0], upVector=[0,1,0], worldUpType='object', worldUpObject=C_LOC)
        B_orient = pm.aimConstraint(C_LOC, B_LOC, aimVector=[1,0,0], upVector=[0,1,0], worldUpType='object', worldUpObject=A_LOC)
        C_orient = pm.aimConstraint(A_LOC, C_LOC, aimVector=[-1,0,0], upVector=[0,-1,0], worldUpType='object', worldUpObject=B_LOC)
        
        A_value = A_LOC.getRotation()
        B_value = B_LOC.getRotation()
        C_value = C_LOC.getRotation()
        
        if not self.debugging:
            pm.delete(A_orient, B_orient, C_orient, A_LOC, B_LOC, C_LOC)
        
        else: 
            print ('Successfully completed the creation and query of guide orientation')
            print A_value, B_value, C_value
        
        return [A_value, B_value, C_value]    
    
    
    ## SETUP FUNCTIONS ##
    def FKIK_create_guides(self, *args):
        print 'FKIK_create_guides activated.', args
        
        pm.select(clear=True)
        
        self.shoulder_guide = pm.joint(position=self.base_pos_list[0], absolute=True)
        self.elbow_guide = pm.joint(position=self.base_pos_list[1], absolute=True)
        self.wrist_guide = pm.joint(position=self.base_pos_list[2], absolute=True)
        
        self.shoulder_guide.rename(self.guide_name_list[0])
        self.elbow_guide.rename(self.guide_name_list[1])
        self.wrist_guide.rename(self.guide_name_list[2])
    
    
    def FKIK_create_joints_from_guides(self, *args):
        print 'Creating FK/IK joint chains on pre-existing guides'
        # Get relevent transformation information
        guide_trans = self.FKIK_query_guide_translation()
        guide_orient = self.FKIK_query_guide_orient()

        # Create joints in place absolute to the world
        pm.select(clear=True)
        self.slave_shoulder = pm.joint(position=guide_trans[0], absolute=True)
        pm.select(clear=True)
        self.slave_elbow = pm.joint(position=guide_trans[1], absolute=True)
        pm.select(clear=True)
        self.slave_wrist = pm.joint(position=guide_trans[2], absolute=True)
        
        # Set individual orientation to avoid issues with joint orientation later.
        self.slave_shoulder.setOrientation(guide_orient[0].asQuaternion())
        self.slave_elbow.setOrientation(guide_orient[1].asQuaternion())
        self.slave_wrist.setOrientation(guide_orient[2].asQuaternion())
        
        # Establish parentage
        self.slave_wrist.setParent(self.slave_elbow)
        self.slave_elbow.setParent(self.slave_shoulder)
        
        # Duplicate for the driver chains
        self.FK_shoulder = pm.duplicate(self.slave_shoulder)[0]
        self.FK_elbow = self.FK_shoulder.getChildren()[0]
        self.FK_wrist = self.FK_elbow.getChildren()[0]
        
        self.IK_shoulder= pm.duplicate(self.slave_shoulder)[0]
        self.IK_elbow = self.IK_shoulder.getChildren()[0]
        self.IK_wrist = self.IK_elbow.getChildren()[0]
        
        # Rename everything
        self.slave_shoulder.rename(self.slave_name_list[0])
        self.slave_elbow.rename(self.slave_name_list[1])
        self.slave_wrist.rename(self.slave_name_list[2])
        
        self.FK_shoulder.rename(self.FK_name_list[0])
        self.FK_elbow.rename(self.FK_name_list[1])
        self.FK_wrist.rename(self.FK_name_list[2])
        
        self.IK_shoulder.rename(self.IK_name_list[0])
        self.IK_elbow.rename(self.IK_name_list[1])
        self.IK_wrist.rename(self.IK_name_list[2])
    
    
    


# Execution of the code
FKIK = FKIK_setup()
FKIK.UI()


#
#FKIK.FKIK_query_guide_orient()
#FKIK.slave_shoulder.setOrientation(FKIK.FKIK_query_guide_orient()[0].asQuaternion())
## End of Code ##
'''
temp_orient = pm.aimConstraint(FKIK.slave_elbow, FKIK.slave_shoulder, aimVector=[1,0,0], worldUpObject=FKIK.slave_wrist)
temp_orientA_value = FKIK.slave_shoulder.getRotation()
FKIK.slave_shoulder.setOrientation(temp_orientA_value.asQuaternion())

pm.datatypes.EulerRotation([0,1,0])
#dir(FKIK.slave_shoulder)
#help(FKIK.slave_shoulder.orientJoint)
#FKIK.slave_shoulder.orientJoint('xyz', zso=True, children=True)











'''