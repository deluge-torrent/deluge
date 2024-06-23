
# Profiling

Profiling helps finding bottlenecks in your program, regarding CPU usage, memory usage and disk (IO) operations.
It may sound advanced, but with the right tools profiling can be quite simple.

Here are some examples from how deluge has been optimized in git master.

## Profiling CPU usage in the GTK UI

Python has [multiple profilers](http://docs.python.org/2/library/profile.html) built in. We'll be using cProfile.

We run deluge in thin client/daemon setup, so running deluge will only start the GTK UI.

### cProfile and Run Snake Run

Running the GTK UI with profiling enabled:

```
 python -m cProfile -o deluge.profile deluge -l deluge.log -L info
```
When you exit deluge, the profile stats are written to the file deluge.profile.

Lets open this with [RunSnakeRun](http://www.vrplumber.com/programming/runsnakerun)

Below is an example of the profile results for version 1.3.5 after connecting to a daemon with 2000 torrents.

![](/deluge_runsnake.png)

A very interresting entry is the update_view in torrentview.py. This function is called 23 times where the total time spent in the function is 27 seconds. Each call takes 1.18 seconds. For the short time the client was connected this is a lot of time!

### line_profiler

Lets examine this function using another tool; [line_profiler](http://packages.python.org/line_profiler/).

After installing line_profiler, we add `@`profile to the function update_view in torrentview.py like this:

```
@profile
def update_view(self, columns=None):
```
and run deluge with kern_prof:

```
kernprof.py -l -v ./deluge -l ~/deluge.log -L info
```
Then connecting to the daemon to load the torrent list and letting it run a few seconds and then close the client.
The output from line_profiler will be printed to the terminal:

```
Wrote profile results to deluge.lprof
Timer unit: 1e-06 s

File: /home/bro/deluge/deluge/ui/gtkui/torrentview.py
Function: update_view at line 402
Total time: 22.7855 s

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   402                                               @profile
   403                                               def update_view(self, columns=None):
   404                                                   """Update the view.  If columns is not None, it will attempt to only
   405                                                   update those columns selected.
   406                                                   """
   407        16          206     12.9      0.0          filter_column = self.columns["filter"].column_indices[0]
   408                                                   # Update the torrent view model with data we've received
   409        16           71      4.4      0.0          status = self.status
   410
   411     34608       172620      5.0      0.8          for row in self.liststore:
   412     34592       255751      7.4      1.1              torrent_id = row[self.columns["torrent_id"].column_indices[0]]
   413
   414     34592      5322894    153.9     23.4              if not torrent_id in status.keys():
   415                                                           row[filter_column] = False
   416                                                       else:
   417     34592     10544768    304.8     46.3                  row[filter_column] = True
   418     34592       347006     10.0      1.5                  if torrent_id in self.prev_status and status[torrent_id] == self.prev_status[torrent_id]:
   419                                                               # The status dict is the same, so do not update
   420     30062        79234      2.6      0.3                      continue
   421
   422                                                           # Set values for each column in the row
   423     40770       112550      2.8      0.5                  for column in self.columns_to_update:
   424     36240       207459      5.7      0.9                      column_index = self.get_column_index(column)
   425     81540       320997      3.9      1.4                      for i, status_field in enumerate(self.columns[column].status_field):
   426     45300       152447      3.4      0.7                          if status_field in status[torrent_id]:
   427     43138       107249      2.5      0.5                              try:
   428                                                                           # Only update if different
   429     43138       118716      2.8      0.5                                  row_value = status[torrent_id][status_field]
   430     43138       252969      5.9      1.1                                  if row[column_index[i]] != row_value:
   431     15377      4731302    307.7     20.8                                      row[column_index[i]] = row_value
   432                                                                       except Exception, e:
   433                                                                           log.debug("%s", e)
   434
   435        16         3291    205.7      0.0          component.get("MenuBar").update_menu()
   436
   437        16        56007   3500.4      0.2          self.prev_status = status
```

Here we see the cummulative stats for this function, i.e. the stats for all the calls to this function combined.
On line 407 we that Hits is 16, which means this method was called 16 times in total. Executing this line 16 times took 206 microseconds.
Looker further down we see some more interesting numbers. Executing line 414 34592 times took a total of 5.3 seconds. Executing line 417 34592 times took 10.5 seconds.
The lines that have no stats, e.g. line 415, were never executed.

Lets do two simple changes:
* Call status.keys() before the for-loop and use the cached results inside the for-loop.
* Add an if-test before line 417 to test if the value is False before setting to True.

These are the new results:

```
Wrote profile results to deluge.lprof
Timer unit: 1e-06 s

File: /home/bro/deluge/deluge/ui/gtkui/torrentview.py
Function: update_view at line 402
Total time: 8.59357 s

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   402                                               @profile
   403                                               def update_view(self, columns=None):
   404                                                   """Update the view.  If columns is not None, it will attempt to only
   405                                                   update those columns selected.
   406                                                   """
   407        16          193     12.1      0.0          filter_column = self.columns["filter"].column_indices[0]
   408                                                   # Update the torrent view model with data we've received
   409        16           66      4.1      0.0          status = self.status
   410        16         5679    354.9      0.1          status_keys = status.keys()
   411     34608       123193      3.6      1.4          for row in self.liststore:
   412     34592       187470      5.4      2.2              torrent_id = row[self.columns["torrent_id"].column_indices[0]]
   413
   414     34592      1541622     44.6     17.9              if not torrent_id in status_keys:
   415                                                           row[filter_column] = False
   416                                                       else:
   417     34592       152303      4.4      1.8                  if row[filter_column] is False:
   418      2162       410067    189.7      4.8                      row[filter_column] = True
   419     34592       235676      6.8      2.7                  if torrent_id in self.prev_status and status[torrent_id] == self.prev_status[torrent_id]:
   420                                                               # The status dict is the same, so do not update
   421     30052        74645      2.5      0.9                      continue
   422
   423                                                           # Set values for each column in the row
   424     40860       105678      2.6      1.2                  for column in self.columns_to_update:
   425     36320       195021      5.4      2.3                      column_index = self.get_column_index(column)
   426     81720       306306      3.7      3.6                      for i, status_field in enumerate(self.columns[column].status_field):
   427     45400       142351      3.1      1.7                          if status_field in status[torrent_id]:
   428     43238       106093      2.5      1.2                              try:
   429                                                                           # Only update if different
   430     43238       117195      2.7      1.4                                  row_value = status[torrent_id][status_field]
   431     43238       231129      5.3      2.7                                  if row[column_index[i]] != row_value:
   432     15367      4591521    298.8     53.4                                      row[column_index[i]] = row_value
   433                                                                       except Exception, e:
   434                                                                           log.debug("%s", e)
   435
   436        16         3417    213.6      0.0          component.get("MenuBar").update_menu()
   437
   438        16        62029   3876.8      0.7          self.prev_status = status
```

Now you can see that line 414 uses 1.5 seconds instead of the previous 5.3.
Also, line 418 (previously 417) uses 400ms instead of 10 seconds in the original code. Most importantly the line is now executed only 2162 times, and not 34592 times as it used to be. Including the the new if-test, the new code uses 560ms compared to 10 seconds in the old.
The reason this is faster can be seen when comparing the time it takes to execute each of the lines one time. The if-test takes 4.4 microseconds on average, while setting the row value to True takes 189 microseconds.

### cProfile and Run Snake Run revisited

Lets do a new profile with the changes to the code:

```
 python -m cProfile -o deluge.profile deluge -l deluge.log -L info
```

![](/deluge_runsnake_after_optimizations.png)

We can now see how update_view has dropped significantly on the list. Each call to update_view now takes 0.37 seconds on average compared to 1.18 in the original code.

## Profiling Deluge daemon with

The daemon can be profiled using the command line option --profile.

```
deluged --profile
```
Deluge 1.3.X uses [hotshot](http://docs.python.org/2/library/hotshot.html). You can convert hotshot profiling data to [KCachegrind](http://kcachegrind.sourceforge.net/html/Home.html) calltree format using hotshot2calltree:

```
hotshot2calltree -o deluged_calltree.profile deluged.profile
```
git-master uses cProfile so the output can be opened directly by [RunSnakeRun](http://www.vrplumber.com/programming/runsnakerun). To open this in KCachegrind (-k option opens the result in KCachegrind automatically):

```
pyprof2calltree -i deluged.profile -k
```

## Profiling memory usage on the Deluge daemon with valgrind (massif)
Be aware that this makes the daemon very slow!

```
valgrind --tool=massif deluged -l ~/deluged.log -L info -d
```
After exiting the daemon, a file named massif.out.<pid> (e.g. massif.out.26034) should've been writen to the working dir.
Lets open that with [massif-visualizer](https://projects.kde.org/projects/extragear/sdk/massif-visualizer)

```
massif-visualizer massif.out.26034
```

<img src="Development Profiling/Deluge_daemon_massif_visualizer.jpg" width=800px>

Here we see a nice graph showing the memory usage at snapshots taken at regular intervals. It's clear that a lot of the memory used by the daemon is in fact used by libtorrent. It's possible to get a more detailed view of the memory usage of the different categories shown in the list on the right.