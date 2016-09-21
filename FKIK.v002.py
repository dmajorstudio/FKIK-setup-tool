'''
Creation of an FKIK setup system

@Author: David Major : major@dmajorstudio.com
@Project: Personal Portfolio
@Company: D Major Studio

Latest update: 2016/09/20 (YYYY/MM/DD)
    - All from scratch : based on work done in class and using better PyMEL examples
'''
import pymel.core as pm


class FKIK_setup(object):
    debugging = True
    cleanup_queue = []
    
    guide_list = []
    slave_JNT_list = []
    FK_JNT_list = []
    IK_JNT_list = []
    
    FKIK_blend_list = []
    
    # Various tool attributes #
    JNT_name_list = ['shoulder_JNT', 'elbow_JNT', 'wrist_JNT']
    JNT_prefix_dict = {'guide':'guide_', 'slave':'slave_', 'FK':'FK_', 'IK':'IK_'}
    
    base_pos_list = [[-5.0, 0.0, 2.0],
                    [0.0, 0.0, 0.0],
                    [4.0, 0.0, 2.0]]
    
    # UI Attributes #
    win_name = 'exampleUI' # Must be a 'legal' name to Maya (A-Z, 0-9, _) !!! No spaces !!!
    window_development = True # A trigger for deleting existing UI window preferences: True / False
    
    # Set up functions: UI first, related functions next.
    ## UI FUNCTION ##
    def UI(self):
        '''
        Generates a basic GUI which can be used to build a functional FKIK arm setup.
        '''
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
                #pm.button( label='Create Orient Helper', command= self.FKIK_query_orientation )
            
        
        # Fix spacing of layout elements
        base.redistribute(.1)
        header.redistribute(1,.1)
        
        # Last lines of code
        self.my_win.show()
        #return [my_win, base, header, btn_ID] # Debugging purposes only
        
    
    ## UTILITY FUNCTIONS ##
    @classmethod
    def FKIK_query_poleVector(self, obj_list, offset_mag=5, *args):
        '''
        Returns a value for positioning a poleVector based off a list of 3 objects.
            - Calculates the midpoint between obj_list[0] and obj_list[2]
            - Calculate the vector from midpoint to obj_list[1]
            - Multiply this vector by given offset_mag to find new position
            @Argument(s):
                obj_list    : A list of 3 transform nodes (shoulder, elbow, wrist)
                offset_mag  : The magnitude of offset projected beyond obj_list[1]
            @Return:
                dt.Vector() - Point position for new poleVector (worldspace)
        '''
        
        # Get vector list
        v_list = self.query_translation(obj_list)
        
        # Setting midpoint
        v_mid = v_list[0]+((v_list[2]-v_list[0])*.5)
        
        # Setting poleVector normal
        v_pv = v_mid+((v_list[1]-v_mid)*offset_mag)
        
        return v_pv
            
    
    
    ## SUPPORTING FUNCTIONS ##
    @staticmethod
    def query_translation(obj_list, *args):
        '''
        Calculate a list of worldspace translation point positions for the given obj_list.
            @Argument(s):
                obj_list : List of objects to obtain translations from.
            @Return: 
                List of dt.Vector()
        '''
        
        return [obj.getTranslation(space='world') for obj in obj_list]
    
    
    @classmethod
    def FKIK_query_orient(self, obj_list, *args):
        '''
        Create aim constraint setup to query properly planar-aligned xyz euler orientations.
            @Argument(s):
                obj_list : List of 3 objects to determine planar relationship
            @Return:
                [[xyz], [xyz], [xyz]]
        '''
        
        if not len(obj_list) == 3:
            raise RuntimeError('Must provide exactly 3 items in obj_list to query orientations correctly.')
        
        POS_list = self.query_translation(obj_list)
        
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
        
        if self.debugging:
            print ('Successfully completed the creation and query of guide orientation')
            print A_value, B_value, C_value
            
        # Add disposable items to the cleanup_queue
        self.cleanup_queue.extend([A_orient, B_orient, C_orient, A_LOC, B_LOC, C_LOC])
        
        return [A_value, B_value, C_value]    
    
    
    ## SETUP FUNCTIONS ##
    def FKIK_create_guides(self, *args):
        '''
        Generate default guides which can be placed arbitrarily in order to
        determine initial placement of joint chains.
            @Attribute(s):
                self.guide_list
        '''
                
        pm.select(clear=True)
        
        guide_shoulder = pm.joint(position=self.base_pos_list[0], absolute=True)
        guide_elbow = pm.joint(position=self.base_pos_list[1], absolute=True)
        guide_wrist = pm.joint(position=self.base_pos_list[2], absolute=True)
        
        guide_shoulder.rename(self.JNT_prefix_dict['guide']+self.JNT_name_list[0])
        guide_elbow.rename(self.JNT_prefix_dict['guide']+self.JNT_name_list[1])
        guide_wrist.rename(self.JNT_prefix_dict['guide']+self.JNT_name_list[2])
        
        self.guide_list = [guide_shoulder, guide_elbow, guide_wrist]
            
    
    def FKIK_create_joints_from_guides(self, *args):
        '''
        Using guides generated from the FKIK_create_guides (stored in self.guide_list),
        create base joint chains which form the FK/IK joint system.
            @Attribute(s):
                self.slave_JNT_list
                self.FK_JNT_list
                self.IK_JNT_list
        '''
        
        # Get relevent transformation information
        guide_trans = self.query_translation(self.guide_list)
        guide_orient = self.FKIK_query_orient(self.guide_list)

        # Create joints in place absolute to the world
        pm.select(clear=True)
        slave_shoulder = pm.joint(position=guide_trans[0], absolute=True)
        pm.select(clear=True)
        slave_elbow = pm.joint(position=guide_trans[1], absolute=True)
        pm.select(clear=True)
        slave_wrist = pm.joint(position=guide_trans[2], absolute=True)
        
        # Set individual orientation to avoid issues with joint orientation later.
        slave_shoulder.setOrientation(guide_orient[0].asQuaternion())
        slave_elbow.setOrientation(guide_orient[1].asQuaternion())
        slave_wrist.setOrientation(guide_orient[2].asQuaternion())
        
        # Establish parentage
        slave_wrist.setParent(slave_elbow)
        slave_elbow.setParent(slave_shoulder)
        
        # Duplicate for the driver chains
        FK_shoulder = pm.duplicate(slave_shoulder)[0]
        FK_elbow = FK_shoulder.getChildren()[0]
        FK_wrist = FK_elbow.getChildren()[0]
        
        IK_shoulder= pm.duplicate(slave_shoulder)[0]
        IK_elbow = IK_shoulder.getChildren()[0]
        IK_wrist = IK_elbow.getChildren()[0]
        
        # Rename everything
        slave_shoulder.rename(self.JNT_prefix_dict['slave']+self.JNT_name_list[0])
        slave_elbow.rename(self.JNT_prefix_dict['slave']+self.JNT_name_list[1])
        slave_wrist.rename(self.JNT_prefix_dict['slave']+self.JNT_name_list[2])
        
        FK_shoulder.rename(self.JNT_prefix_dict['FK']+self.JNT_name_list[0])
        FK_elbow.rename(self.JNT_prefix_dict['FK']+self.JNT_name_list[1])
        FK_wrist.rename(self.JNT_prefix_dict['FK']+self.JNT_name_list[2])
        
        IK_shoulder.rename(self.JNT_prefix_dict['IK']+self.JNT_name_list[0])
        IK_elbow.rename(self.JNT_prefix_dict['IK']+self.JNT_name_list[1])
        IK_wrist.rename(self.JNT_prefix_dict['IK']+self.JNT_name_list[2])
    
        self.slave_JNT_list = [slave_shoulder, slave_elbow, slave_wrist]
        self.FK_JNT_list = [FK_shoulder, FK_elbow, FK_wrist]
        self.IK_JNT_list = [IK_shoulder, IK_elbow, IK_wrist]
        
        # Run internal functions
        self.FKIK_connect_arms()

    
    def FKIK_connect_arms(self):
        '''
        Create connections between joint chains.
            @Attribute(s):
                self.FKIK_blend_list
        '''
        blend_list = []
        for x in range(3):
            blend_node = pm.createNode('blendColors')
            blend_list.append(blend_node)
            
            self.FK_JNT_list[x].rotate >> blend_node.color1
            self.IK_JNT_list[x].rotate >> blend_node.color2
            blend_node.output >> self.slave_JNT_list[x].rotate
        
        self.FKIK_blend_list = blend_list

    # TO-DO:
    #     - Create controller setup to connect to self.FKIK_blend_list
    #     - Create FK arm controller hierarchy + connect to FK joints
    #     - Create IK arm controls (complete with poleVector constraint)
    #     - Work on setting up FK/IK switch/position snapping.
        

# Execution of the code
FKIK = FKIK_setup()
FKIK.UI()

## End of Code ##
