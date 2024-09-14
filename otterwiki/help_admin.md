## Admin Guide

An Otter Wiki can be configured by Admin users who can find <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-cogs"></i></span> Application Preferences</span>, <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-users"></i></span> User management</span> etc. in the sidebar menu of
their <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span> <i class="fas fa-caret-right"></i> <span class="btn btn-square btn-sm"><i class="fas fa-cog"></i></span> Settings</span>.

### Branding

In the <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-cogs"></i></span> Application Preferences</span> the <span class="help-button">Site Name</span>, which is
displayed in the navigation bar on the top of the site and in emails, can be
configured.

The <span class="help-button">Site Logo</span> is displayed next to the site
name, while the <span class="help-button">Site Icon</span> (or favicon) is displayed in the
browser tab and in bookmarks. Both Site Logo and Site Icon can be attachments.
An Otter Wikis logo is the default for both.

The <span class="help-button">Site Description</span> is used in the
`<meta name="description">` tag.

To hide the logo of An Otter Wiki, check <span class="help-button"><input type="checkbox" style="display:inline;" id="hide-logo" checked> Hide logo of an An Otter Wiki n the sidebar</span>. A menu item linking the about information will be added to the <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-ellipsis-v"></i></span></span> menu.

### User management

All users are listed in a table under <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-users"></i></span> User management</span>. You can update the flags of the users by checking and unchecking the checkboxes, where <span class="help-button"><input type="checkbox" style="display:inline;" id="true" checked></span> means the flag is set and <span class="help-button"><input type="checkbox" style="display:inline;" id="false"></span> means the flag is not set. A set flag grants a privilege to a user.

Privileges granted per user add to the general permissions. For example, if in general only users with the **Admin** flag are allowed to upload attachments, the `user@example.org` can be allowed to Upload without being flagged as Admin.

A user with a <span class="help-button"><input type="checkbox" style="display:inline;" id="true-admin" checked></span> in the **Admin** column has Admin permissions. The changes are applied with <span class="btn btn-primary btn-sm btn-hlp">Update Privileges</span>.

#### Edit a user

With <span class="help-button"><a hre="#"><i class="fas fa-user-edit"></i></a></span>
you can open up a single user for editing. Here you can update
<span class="help-button">Name</span> and <span class="help-button">eMail</span>
of a user, and set flags and permissions. Changing a users name or email does not change
the commit history and only affects future commits.

Like in the User management table you can control the users flags using the
checkboxes.

The changes will be applied with <span class="btn btn-primary btn-sm btn-hlp">Update</span>.

#### Delete a user

On the Edit user page you can remove a user from the wiki's database. Check the
box and hit <span class="btn btn-danger btn-sm btn-hlp" style="border: None;" role="button">Delete</span>.
Note that this will not change any edit history or prevent the user from signing up again.

### Sidebar Preferences

#### Shortcuts
Frequently used Wiki features such as <code>Home</code>, the <code>Page Index</code>, the <code>Changelog</code> or <code>Create
Page</code> can be added to the Sidebar, e.g. <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-list"></i></span> A - Z</span>.

#### Custom Menu

A custom menu can be configured to display links to important pages or external links.
For wiki pages, only the page name needs to be entered. For external links, enter the
link with its full URL. Optionally, a title can be specified for each entry. The order
of the entries in the menu is set manually.

#### Page Index

The Sidebar can be configured to display the Page Index in different modes.
You can display pages and directories either alphabetical, or with directories first,
or only the directories. Alternatively you choose to not display the Page Index at all.

### Content and Editing Preferences

#### Commit Messages
Per default An Otter Wiki requires users to add commit messages when updating a
page. You can configure this with the <span class="help-button">Commit Message</span>
setting. Setting this to `optional` will allow empty commit messages.

#### Page case name
An Otter Wiki stores pages in files with names of all lowercase names. To retain
the upper and lower case of the filenames, check <span class="help-button"><input type="checkbox" style="display:inline;" id="true-retain-page-name" checked> Retain page name case</span>.

#### Git Web server
With <span class="help-button"><input type="checkbox" style="display:inline;" id="true-git-webserver" checked> Enable Git Server</span> allow users with the permission to READ to clone and pull the wiki content via git and users with UPLOAD/Attachment management permissions to push content. HTTP Basic authentication is used for non anonymous access. There is no option for using git via ssh. When enabled, users find the URL to clone the repositroy in their settings.


### Access Permissions and Registration Preferences

What is necessary for a user to be able to Read/Write pages or upload and modify
attachments is controlled in the <span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-users-cog"></i></span> Permissions and Registration Preferences</span>.

- `Read Access` enables users to display pages and attachments. Including the
    history and every single commit.
- `Write Access` enables users to edit pages.
- `Attachments Access` enables users to upload and modify attachments.

Who can access what is defined via

- `Anonymous` - Everyone can access the wiki without being logged in.
- `Registered` - Users need an account and have to be logged in.
- `Approved` - Users have to be logged in and the <span class="help-button">Approved</span> flag has to be set.
- `Admin` - Users have to be logged in and the <span class="help-button">Admin</span> flag has to be set.

Additionally, you can configure privileges per user. The privileges granted per user add to the general permissions. See [User Management](#user-management) above.

With <span class="help-button"><input type="checkbox" style="display:inline;" id="true-reg-req" checked> Disable registration</span> you can disable that anyone can sign up for a new account.

Configure <span class="help-button"><input type="checkbox" style="display:inline;" id="true-reg-req" checked> Registration requires email confirmation</span>, to ask users to confirm their email address, before their account is enabled. This is supposed to prevent users to register with a typo in their address or even using a fake mail address.

If a user needs to be approved, an admin user either needs to set the flag manually
or enable <span class="help-button"><input type="checkbox" style="display:inline;" id="true-auto-approve" checked> Auto approve of newly registered users</span>. When admins need
to approve users, <span class="help-button"><input type="checkbox" style="display:inline;" id="true-notify" checked> Notify admins on new user registration</span> helps with that.
For more convenience, enable <span class="help-button"><input type="checkbox" style="display:inline;" id="true-notify" checked> Notify users when their account has been approved</span> so
that users are notified automatically and there is no need to notify them
yourself.


### Mail Preferences

To enable An Otter Wiki to send mails to users registering, resetting their lost
password and notify admins about new users, configure the
<span class="help-button"><span class="btn btn-square btn-sm"><i class="fas fa-envelope"></i></span> Mail Preferences</span>. See the [flask-mail documentation](https://pythonhosted.org/Flask-Mail/) for configuration details.

You can test the configuration using <span class="help-button">Send Test Mail</span>. Per default the test mail is sent to yourself.


[modeline]: # ( vim: set fenc=utf-8 spell spl=en sts=4 et tw=80: )
