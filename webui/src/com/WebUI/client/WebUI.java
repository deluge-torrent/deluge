/* 
 Copyright (c) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2, or (at your option)
 any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
*/

package com.WebUI.client;

import java.lang.Throwable;
import java.lang.System;

//import java.util.Map;
//import java.util.HashMap;
import java.util.Iterator;

//import com.google.gwt.user.client.ui.ClickListener;
import com.google.gwt.user.client.ui.Label;
//import com.google.gwt.user.client.HistoryListener;

import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Command;
import com.google.gwt.core.client.EntryPoint;

import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.Widget;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.DockPanel;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.SourcesTableEvents;
import com.google.gwt.user.client.ui.TableListener;

import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestException;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.Response;
import com.google.gwt.http.client.RequestTimeoutException;

import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.json.client.JSONObject;

public class WebUIUtilities {
	public static String round(double value, int places) {
		String ret = String.valueOf(value);
		int temp = ret.indexOf(".");

		if (temp == -1) {
			return ret;
		}

		return (ret.substring(0, temp + places));
	}

	public static String getDataRate(double value) {
		return (getDataAmount(value) + "/s");
	}

	public static String getDataAmount(double value) {
		double val = 0;
		String units;

		if (value < 1048576) {
			val   = value / 1024.0;
			units = "KB";
		} else if (value < 1073741824) {
			val   = value / 1048576.0;
			units = "MB";
		} else {
			val   = value / 1073741824.0;
			units = "GB";
		}

		return (round(val, 2) + " " + units);
	}

	public static native void gotoURL(String newURL) /*-{
		window.alert(location.href);
		location.href = "www.cnn.com";
		window.alert(location.href);
	}-*/;
}

public class TorrentInfo {
	public long   unique_ID;
	public long   queue_pos;
	public String name;
	public double download_rate;
	public double upload_rate;
	public long   total_seeds;
	public long   total_peers;
	public long   num_seeds;
	public long   num_peers;
}

public class TorrentListAction implements TableListener {
	private TorrentList mainList;

	public TorrentListAction(TorrentList list) {
		mainList = list;
	}

	public void onCellClicked(SourcesTableEvents sender, int row, int cell) {
	// Select the row that was clicked (-1 to account for header row).
		if (row > 0)
			mainList.selectRow(row - 1);
	}
}

public class TorrentList extends FlexTable {
	private int               selectedRow = -1;
	private TorrentListAction action = new TorrentListAction(this);
	private TorrentInfo[]     oldTorrents = null;

	public void init() {
		setStyleName("torrentlist");
		setCellSpacing(0);
		setCellPadding(2);

		// Headers row
		setText(0, 0, "#"); // We need a hashmap for names to columns, for the future
		setText(0, 1, "Name");
		setText(0, 2, "Seeds");
		setText(0, 3, "Peers");
		setText(0, 4, "Download");
		setText(0, 5, "Upload");
		getRowFormatter().addStyleName(0, "torrentList-Title");

		addTableListener(action);
	}

	public void applyTorrents(TorrentInfo[] torrents) {
//Window.alert("Applying torrents in tablelist");
		// Add new torrents and update existing ones
		for (int x = 0; x < torrents.length; x++) {
			int tempIndex = getIndexByUniqueID(torrents[x].unique_ID);
			if (tempIndex == -1) {
				tempIndex = getRowCount()-1; // (-1 because of headers)
			}
			updateTorrent(tempIndex, torrents[x]);
		}

		// Delete torrents no longer with us. CHANGE selectedRow to -1 if the selected row is dead!
		// ...

		// Save the new torrents, for the next comparison
		oldTorrents = torrents;

		// Select a row, if none is currently selected
		if (getRowCount() > 1 && selectedRow == -1) {
//			Window.alert("Selecting 1");
			selectRow(0);
		} else {
//			Window.alert("No Selecting");
		}
	}

	private int getIndexByUniqueID(long unique_ID) {
		if (oldTorrents == null) {
			return -1;
		}

		for (int x = 0; x < oldTorrents.length; x++) {
			if (oldTorrents[x].unique_ID == unique_ID) {
				return x;
			}
		}

		return -1;
	}

	private void updateTorrent(int row, TorrentInfo torrent) {
		row = row + 1;
//Window.alert("Updating torrent in tablelist: " + String.valueOf(row));
		setText(row, 0, String.valueOf(torrent.queue_pos)+1); // Humans like queues starting at 1
		setText(row, 1, torrent.name);
		setText(row, 2, String.valueOf(torrent.num_seeds) + " (" +
		                   String.valueOf(torrent.total_seeds) + ")");
		setText(row, 3, String.valueOf(torrent.num_peers) + " (" +
		                   String.valueOf(torrent.total_peers) + ")");
		setText(row, 4, WebUIUtilities.getDataRate(torrent.download_rate));
		setText(row, 5, WebUIUtilities.getDataRate(torrent.upload_rate));
		setWidth("100%");
	}

	public void selectRow(int row) {
		styleRow(selectedRow, false);
		styleRow(row, true);

		selectedRow = row;
//    Mail.get().displayItem(item);
	}

	private void styleRow(int row, boolean selected) {
		if (row != -1) {
			if (selected)
				getRowFormatter().addStyleName(row + 1, "torrentList-SelectedRow");
			else
				getRowFormatter().removeStyleName(row + 1, "torrentList-SelectedRow");
		}
	}}

public class WebUIApp implements EntryPoint {

	private static final int STATUS_CODE_OK = 200;
	private static final int TIMEOUT        = 3000;
	private static final int TIMER          = 2000; // SHOULD BE 1000 - but more allows for debug
	private static final int MAX_TIMER      = TIMEOUT/TIMER;

	private DockPanel   panel       = new DockPanel();
	private MenuBar     menu        = new MenuBar();
	private TorrentList torrentList = new TorrentList();
	private Label       statusBar   = new Label();

	private Request       currRequest;
	private boolean       waiting     = false;
	private int           currTimer   = 0;
	private JSONValue     torrentsJSON;
	private TorrentInfo[] currTorrents;

	public void onModuleLoad() {
//Window.alert("Module Load");

		// Buttons
//		final Button button = new Button("Click here...");

		// Menus
		MenuBar menu0 = new MenuBar(true);

		menu0.addItem("Quit", true, new Command() {
				public void execute() {
					doPost("/", "quit", new RequestCallback() {
						public void onResponseReceived(Request request, Response response) {
						}
						public void onError(Request request, Throwable e) {
						}
					});

					// Move to new page, a "bye" page.
					quit();
//					WebUIUtilities.gotoURL("about:blank");
//					Window.alert("Bye.");
				}
			});

		menu.addItem(new MenuItem("File", menu0));
		menu.setWidth("100%");

		// Table list
		torrentList.init();
//		torrentList.addTorrent("a.torrent");

//		torrentList.selectRow(0);

		// Timer
		Timer t = new Timer() {
			public void run() {
				heartBeat();
			}
		};

		t.scheduleRepeating(TIMER); //

		// Set up main panel
		RootPanel.get().setStyleName("webui-Info");

		panel.add(torrentList, DockPanel.CENTER);
//		panel.add(statusBar,   DockPanel.SOUTH);

		RootPanel.get().add(menu);
		RootPanel.get().add(panel);
		RootPanel.get().add(statusBar);
//Window.alert("end Module Load");
	}

	private void quit() {
		RootPanel.get().remove(menu);
		RootPanel.get().remove(panel);
		RootPanel.get().remove(statusBar);
	}

	// Called once per TIMER tick (usually 1 second?)
	private void heartBeat() {

		// FOR NOW, just do it to fill torrentsJSON, that's it
//		if (torrentsJSON == null) {

		if (true) { // We always tick, don't we?
			// Send and/or cancel current server request
			if (!waiting || currTimer == MAX_TIMER) {
				if (currRequest != null) {
					currRequest.cancel();
				}
				doPost("/", "list", new RequestCallback() {
					public void onResponseReceived(Request request, Response response) {
						waiting = false;
	
						if (STATUS_CODE_OK == response.getStatusCode()) {
							setStatusBar("Server responding.");// + response.getText());
							torrentsJSON = JSONParser.parse(response.getText());
							updateTorrentList();
						} else {
							setStatusBar("Server gives an error: " + response.getHeadersAsString() + "," + response.getStatusCode() + "," + response.getStatusText() + "," + response.getText());
						}
					}

					public void onError(Request request, Throwable e) {
						waiting = false;

						if (e instanceof RequestTimeoutException) {
							setStatusBar("Server timed out.");// + e.getMessage());
						} else {
							setStatusBar("Server gave an ODD error: " + e.getMessage());
						}
					}
				});

//				setStatusBar("Sent request...");
				waiting   = true;
				currTimer = 0;
			} else {
//				setStatusBar("Still waiting..." + String.valueOf(currTimer));
				currTimer = currTimer + 1;
			}
		} else {
			setStatusBar("Core off.");
		}
//		} // FOR NOW

		// Update torrent list?
//		updateTorrentList();
	}

	private void setStatusBar(String text) {
		statusBar.setText(String.valueOf(System.currentTimeMillis()) + ":" + text);
//		statusBar.setText(String.valueOf(System.currentTimeMillis()) + ":" + text + "\r\n<br>" + statusBar.getText());
	}

	// Need to allow different callbacks from the post...
	private void doPost(String url, String postData, RequestCallback callback) {
		RequestBuilder builder = new RequestBuilder(RequestBuilder.POST, url);
		builder.setTimeoutMillis(TIMEOUT);

		try {
			currRequest = builder.sendRequest(postData, callback);
		} catch (RequestException e) {
			waiting = false;
			setStatusBar("Failed to send a POST request: " + e.getMessage());
		}
	}

	// Update torrent list, using torrentsJSON (which was updated in the POST callback)
	private void updateTorrentList() {
		if (torrentsJSON == null) {
			return;
		}
//Window.alert("UpdateTorrentList - got torrentsJSON");
		currTorrents = new TorrentInfo[torrentsJSON.isArray().size()];

		JSONObject    curr;

		for (int x = 0; x < torrentsJSON.isArray().size(); x++) {
			curr = torrentsJSON.isArray().get(x).isObject();

			currTorrents[x] = new TorrentInfo();
			currTorrents[x].unique_ID     = (long) curr.get("unique_ID").isNumber().getValue();
			currTorrents[x].queue_pos     = (long) curr.get("queue_pos").isNumber().getValue();
			currTorrents[x].name          = curr.get("name").isString().stringValue();
			currTorrents[x].download_rate = curr.get("download_rate").isNumber().getValue();
			currTorrents[x].upload_rate   = curr.get("upload_rate").isNumber().getValue();
			currTorrents[x].total_seeds   = (long)curr.get("total_seeds").isNumber().getValue();
			currTorrents[x].total_peers   = (long)curr.get("total_peers").isNumber().getValue();
			currTorrents[x].num_seeds     = (long)curr.get("num_seeds").isNumber().getValue();
			currTorrents[x].num_peers     = (long)curr.get("num_peers").isNumber().getValue();
		}

		torrentList.applyTorrents(currTorrents);
//Window.alert("end UpdateTorrentList");
	}

	// A debug convenience function
	private void dumpJSON(JSONValue value) {
		if (value.isArray() != null) {
			Window.alert("Array; size: " + String.valueOf(value.isArray().size()));

			for (int x = 0; x < value.isArray().size(); x++) {
				dumpJSON(value.isArray().get(x));
			}
		} else if (value.isBoolean() != null) {
			Window.alert("Boolean" + String.valueOf(value.isBoolean().booleanValue()));
		} else if (value.isNull() != null) {
			Window.alert("NULL");
		} else if (value.isNumber() != null) {
			Window.alert("Number" + String.valueOf(value.isNumber().getValue()));
		} else if (value.isObject() != null) {
			Window.alert("Object size: " + String.valueOf(value.isObject().size()));

			Iterator  it = value.isObject().keySet().iterator();
			String    key;
			for (int x = 0; x < value.isObject().size(); x++) {
				key = String.valueOf(it.next());
				Window.alert("(Key:)" + key);
				dumpJSON(value.isObject().get(key));
			}
		} else if (value.isString() != null) {
			Window.alert("String: " + value.isString().stringValue());
		} else {
			Window.alert("WHAT IS THIS JSON?!");
		}
	}

}




/*public class MenuAction implements Command {
	public void execute() {
		Window.alert("Thank you for selecting a menu item.");
//		Window.alert("Thank you for selecting a menu item.");
	}
}*/

/*
Map<String, String> phoneBook = new HashMap<String, String>();
phoneBook.put("Sally Smart", "555-9999");
phoneBook.put("John Doe", "555-1212");
phoneBook.put("J. Random Hacker", "555-1337");

The get method is used to access a key; for example, the value of the expression phoneBook.get("Sally Smart") is "555-9999".
*/





/*    final Label label = new Label();
//		History.addHistoryListener(this);
//				Window.alert("Nifty, eh?");

    button.addClickListener(new ClickListener() {
      public void onClick(Widget sender) {
        if (label.getText().equals(""))
          label.setText("Good, it works.");
        else
          label.setText("");
      }
    });

    // Assume that the host HTML has elements defined whose
    // IDs are "slot1", "slot2".  In a real app, you probably would not want
    // to hard-code IDs.  Instead, you could, for example, search for all 
    // elements with a particular CSS class and replace them with widgets.
    //
    RootPanel.get("slot1").add(button);
    RootPanel.get("slot2").add(label);
*/


/*	private HashMap parsePythonDict(String pythonDict) {
		HashMap ret = new HashMap();
		int startIndex, endIndex = 0;
		String key, val;

		while (pythonDict.indexOf("'", endIndex + 1) != -1) {
			startIndex = pythonDict.indexOf("'", endIndex   + 1) + 1;
			endIndex   = pythonDict.indexOf("'", startIndex + 1);
			key = pythonDict.substring(startIndex, endIndex);

			startIndex = endIndex + 3;
			endIndex   = pythonDict.indexOf(",", startIndex + 1); // BUG POTENTIAL
			if (endIndex == -1) {
				endIndex = pythonDict.lastIndexOf("}");
			}
			val = pythonDict.substring(startIndex, endIndex);

			ret.put(key, val);
			Window.alert(key + " :: " + val);
		}

		return ret;
	}*/
