def save_matlab(data, filename='', dirname='./', save_piezo=True, save_command=True):
    """
    Save the data stored in a recording object in matlab files in a directory.
    Parameters:
    data - `Recording` object
    filename [string] - name for the directory and the files
        -- this should be only the NAME OF THE FILE, not the path and it should not contain
        -- stupid characters like '/' etc
    dirname [string] - name of the directory
    save_piezo [bool] - should save the piezo data
    save_command [bool] - what about the command voltage data
    
    Returns:
    True if successfully saved
    False if a directory with the given name already exists
    """
    
    # if no filename is specified we use the name of the file that was loaded
    if not filename:
        filename = data.filename+'_SAVE'
        
    N = len(filename)
    for i, char in enumerate(filename[::-1]):
        # loop over the full filename (which includes directory) backwards
        # to extract the extension and name of the file
        if char=='.':
            period = N-i
        if char=='/':
            slash = N-i
            break
    filename = filename[slash:period-1]
    filename = ''.join(filename.split())
    
    # create a direcotry in which to save the data
    dirname+=filename
    dirname+='/'
    try: 
        os.mkdir(dirname)
    except FileExistsError:
        # mkdir cannot create a directory if it already exists
        # if this happens do not save anything
        print("""Data not saved!! \n A directory by that name already exists.
            \n Please choose a new name.""")
        return False
    # save each series seperatly
    for datakey, series in data.items():
        file_to_save = dirname+filename+'_'+datakey+'.mat'
        #dictionary for saving a series to matlab
        savedict = {}
        savedict['time'] = raw[0]['time']
        # need this to add leading zeros to episode number in filename
        no_episodes = len(series)
        fill_length = len(str(no_episodes))
        #fill savedict
        for episode in series:
            for name, value in episode.items():
                if name == 'time':
                    continue
                elif name == 'piezo' and not save_piezo:
                    continue
                elif name == 'command' and not save_command:
                    continue
                else:
                    n = str(episode.nthEpisode)
                    n = n.zfill(fill_length)
                    savedict[name+n] = value
        #save to file
        io.savemat(file_to_save,savedict)
    return True