# UAV Processing Platform

The project was initiated as a way to simplify the process of documenting, structuring and reviewing drone flights done at Vollebekk for the Norwegian infrastructure for phenotyping. 

If is mostly built in Python with Django, but has some javascript elements for some frontend functionality.

## Requirements

To run the program you need Docker, which then will install the needed packages.

## Installation

First you need to clone the github repo with 
```bash
https://github.com/fahadijaz/UAV-Data-Processing.git
```
then
```bash
cd UAV-Data-Processing/processing_platform
```
now you can bring docker up with
```bash
docker compose up --build -d
```
to import the flight log you need to run
```bash
docker compose exec web python3 manage.py import_flight_logs "<path to excel file>"
```
here you can use the root download simply by doing "downloads/Drone Flying Schedule 2025.xlxs"

## Structure

#### Flight overview

Here you can filter the flights by different parameters to find the flights you want. When you have found the wanted flight you can double click the row for detailed information.

#### Weekly overview

This is targeted at the drone pilots and operators to keep track of what flights were flown that week. It displays both it has been flown and if it has been processed.

#### Data visualization

The Data visualization page takes in an excel files and plots and displays information for the different plots throughout the season. Here you can see different spectres of the light spectrum in a box plot.

#### Easy Growth 

Displaying the temperature and humidity for each plot

#### SD - card

This is not working due to limitations of browsers accessing local drives and is built into Django and other frameworks. To get this working we must turn it into a desktop app. Here Electron might be an idea, but probably a better idea, would be to rewrite to Rust and use Tauri.

## Technical structure


## Licence
