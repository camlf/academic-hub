# Hub OCS Accounts and Namespaces Structure 

Version 1, 4/28/2020

This document is a draft how to structure accounts, roles and namespaces so that it's possible to manage easily and move from fully open access to more restrictive scenario without having to migrate or perform account/roles reshuffling. 

We first introduce the OCS components and concepts necessary. Second section is about Hub structure we impose on those component to meet our goals. 

## OCS components and concepts

### User accounts

Fields: 
* [I] First name
* [I] Last name
* [I] Email
* [O] Sign In
* [I] IdP
* [O] Status 

Legend: [I] == input, [O] from OCS 

Neville and James W. suggested we standardize on Google as the IdP (4/1/2020 meeting)

Each user is assigned one or more roles. Everyone has the "Account Member" role which cannot be removed. 

### Roles  

A number of roles are already defined with each new OCS tenant. They are with their permissions: 

* **Account Member:** Log in and access the OCS portal. Users may be assigned one or more user roles, but all users are assigned the Account Member role.
* **Account Administrator:** Add, edit, remove, and edit the permissions of existing users.
* **Account {Contributor, Data Steward, Viewer}:** Currently, those roles do not yet grant the user any inherent privileges; they are reserved for future use as new OCS features are introduced.

Within OCS portal, for a given role it's possible to list users assigned and unassigned and move users from one list to the other. 

### Namespaces, Streams and Data Views

Each OCS tenant can host up to 5 namespaces. A namespace contains a finite number of streams, each stream being a collection of sequentially occurring values indexed by a single property, typically time series data. A namespace also contains Data views which are subsets of data from one or more streams, which can serve as a bridge between raw stream data and data-driven applications.

Given the limited number of namespaces, multiple data sets would share a same namespace. Here is a possible structure:

* HubData: hosted data sets: Deschutes, UC Davis, 
* ExperimentData: real-time data from experiment 
* \<Special project>: e.g. HackDavis 
* Development: restricted access
* \<Spare namespace>

Access control for each namespace, stream and data view is managed by assigning permissions to Roles in the tenant. According to the OCS documentation: 

*Users will be able to perform an access operation (read, write, delete, or manage permissions) if 		they have a role which is assigned an access type of Allow and they do not have a role which is assigned an access type of Deny for that operation. The user or application who created a resource, identified as the Owner, is always guaranteed complete access on that resource.*

![](https://academichub.blob.core.windows.net/images/ocs-manage-permissions.jpg)

## Hub Structure 

### Student Accounts

On top of the standard OCS user fields listed before, some additional information about an AH student are:

* University 
* Class attended
* Expiration 

The university + class will inform the student data access. [QUESTION: should a role be university+class or just university? Do we foresee multiple classes per one institution requiring different access?]

Expiration date controls when the account should be deleted. 

### Class onboarding workflow

1. [S?] eSLA executed with / max # of concurrent students / max # of concurrent classes
2. [S?] Designation of one or two on-site Hub admin (OSHA) 
3. [H] Registration of class(es), # of students per class 
3. [H] Information given to students to self-register: URL, university, class, token(?)
4. [H] OSHA should grant/deny access to registered students
5. [HO] Each grant launch the OCS user
6. [H] OSHA can check status of student OCS account (Pending, Active)
7. [?] Distribution of hub material to students 

Legend: S == Salesforce, H == hub application, O == OCS  

### Student onboarding workflow

1. [H] Registration using info received from OSHA
2. [H] Verification of account status (waiting approval, approved, OCS invite sent, active)
3. [O] Verification of data access with self-check notebook 
4. [?] Else?

### Data Sources

1. Raw PI System Dumps: e.g. next Deschutes
2. PItoOCS: from PI3 Hub to OCS, trial with UC Davis waiting for next version of PItoOCS (finer tag selection) to resume
3. CSV portal upload: Utah, Mines
4. FogLAMP(OPC-UA) / OMF: Rose-Hulman, McMaster
5. BYU Board
6. Student computation: future 

### Namespace data sharing

Need a similar mechanism as AF with different databases to gather logically related data streams. We just to have to agree on a convention, e.g. having a common metadata key `asset_db`. A stream will belong to only one database. 

PItoOCS controls both stream ID and stream name. `asset_db` need to be added separately on those streams.  `asset_db` should become an important filter since access control for a given role (in our case a university-class) is highly likely to be done at the database level (note that ACL is done at the stream level, so some script will be needed to map an "asset_db access"  to streams).
