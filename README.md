# rqlite snap

This is a snap of rqlite, a highly available SQLite. rqlite is a distributed
relational database, which uses SQLite as its storage engine. rqlite uses
Raft to achieve consensus across all the instances of the SQLite databases,
ensuring that every change made to the system is made to a quorum of SQLite
databases, or none at all. It also gracefully handles leader elections, and
tolerates failures of machines, including the leader.

## Building

To build this snap:

```
  git clone https://github.com/markshuttle/rqlite-snap.git
  cd rqlite-snap
  snapcraft
```

To install this snap (unsigned) after building:

```
  sudo snap install --force-dangerous rqlite_<version>.snap
```

## TODO

 * join and leave commands


