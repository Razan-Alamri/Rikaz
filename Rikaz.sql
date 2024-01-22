-- Create the User table
CREATE TABLE User (
    userID INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT,
    lastName TEXT,
    Email TEXT,
    Password TEXT
);

-- Create the SatelliteImage table
CREATE TABLE SatelliteImage (
    imageID INTEGER PRIMARY KEY AUTOINCREMENT,
    imageName TEXT,
    satelliteImage BLOB,
    satelliteName TEXT,
    Coordinates TEXT,
    areaName TEXT,
    Resolution TEXT,
    Timestamp TEXT,
    userID INTEGER,
    FOREIGN KEY (userID) REFERENCES User(userID)
);

-- Create the Result table
CREATE TABLE Result (
    resultID INTEGER PRIMARY KEY AUTOINCREMENT,
    Map BLOB,
    Timestamp TEXT,
    userID INTEGER,
    imageID INTEGER,
    FOREIGN KEY (userID) REFERENCES User(userID),
    FOREIGN KEY (imageID) REFERENCES SatelliteImage(imageID)
);

-- Create the Mineral table
CREATE TABLE Mineral (
    mineralID INTEGER PRIMARY KEY AUTOINCREMENT,
    mineralName TEXT,
    mineralDescription TEXT
);

-- Create the ResultMineral table to represent the many-to-many relationship between Result and Mineral
CREATE TABLE ResultMineral (
    resultID INTEGER,
    mineralID INTEGER,
    PRIMARY KEY (resultID, mineralID),
    FOREIGN KEY (resultID) REFERENCES Result(resultID),
    FOREIGN KEY (mineralID) REFERENCES Mineral(mineralID)
);

-- sqlite3 Rikaz.db -init Rikaz.sql