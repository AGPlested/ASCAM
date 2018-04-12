from scipy import io
import os

def save_matlab(data, filename='', save_piezo=True,
                save_command=True):
    """
    Save the series stored in a recording object in matlab files in a directory.
    Parameters:
    data - `Recording` object
    filename [string] - name for the directory and the files this should be only
                        the NAME OF THE FILE, not the path and it should not
                        contain problematic characters like '/' etc
    dirname [string] - name of the directory
    save_piezo [bool] - should save the piezo data
    save_command [bool] - what about the command voltage data

    Returns:
    True if successfully saved
    False if a directory with the given name already exists
    """
    return_status = False
    # if no filename is specified we use the name of the file that was loaded
    if not filename:
        filename = './'+data.filename+'_SAVE'

    # this next bit of code is supposed to
    N = len(filename)
    period = False
    slash = False
    for i, char in enumerate(filename[::-1]):
        # loop over the full filename (which includes directory) backwards
        # to extract the extension and name of the file
        if char=='.':
            period = N-i
        if char=='/':
            slash = N-i
            break
    # this if statement seperates the variable `filename` into the full path in `dirname`
    # and keeps everything after the last slash except the extension to name the
    # actual saved files in the directory
    if period and slash:
        dirname = filename[:period-1]
        filename = filename[slash:period-1]
    elif slash and not period:
        dirname = filename
        filename = filename[slash:]
    # replace whitespaces in dirname and filename and with underscore
    dirname = '_'.join(dirname.split())
    filename = '_'.join(filename.split())

    try:
        os.makedirs(dirname)
    except OSError:
        # mkdir cannot create a directory if it already exists
        # if this happens do not save anything
        print("""A directory by that name already exists, make sure everything went well.""")
    finally:
        # save each series seperatly
        for datakey, series in data.items():
            file_to_save = dirname+'/'+filename+'_'+datakey+'.mat'
            #dictionary for saving a series to matlab
            savedict = {}
            savedict['time'] = series[0]['time']
            # need this to add leading zeros to episode number in filename
            no_episodes = len(series)
            fill_length = len(str(no_episodes))
            #fill savedict
            for episode in series:
                for name, value in episode.items():
                    # the if statements skip the items that do not need to be
                    # saved
                    if name == 'time':
                        continue
                    elif name == 'piezo' and not save_piezo:
                        continue
                    elif name == 'command' and not save_command:
                        continue
                    else:
                    # add data to dictionary
                        n = str(episode.nthEpisode)
                        n = n.zfill(fill_length)
                        savedict[name+n] = value
            #save to file
            io.savemat(file_to_save,savedict)
            return_status = True
    return return_status
