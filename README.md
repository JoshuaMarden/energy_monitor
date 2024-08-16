# Energy Monitor

## Description
#### A dashboard for the monitoring of energy metrics and such as price, demand, or carbon production. See how much of your electricity is generated by nuclear fission, check the cheapest time to charge your electric campervan, or just have a curious glance at what's going on in the grid we all depend upon.

(Python 3.12> and MacOS. You will need Amazon AWS and your login credentials.)

## 'Visuals'
! We'll add some visuals here maybe, using [Asciinema](https://asciinema.org/) or using [ttygif](https://github.com/icholy/ttygif) and a recording. !

## Badges
! Are we doing badges? !

## Installation
[Clone the repo](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) from github.

In terminal, navigate to the root directory of the repository `energy_monitor`.
Run the following commands:
-`python3 -m venv .venv`
-`bash setup.sh` ! we might want a simple setup script !
-`source .venv/bin/activate`
-`pip3 install requirements.txt`

Once you have done this, you should be able to run Energy Monitor by running `python3 run.py` from within the repository. No need to run the other steps again.

! definitely a demo here using [Asciinema](https://asciinema.org/) ! 

## Data Sources & Design Choices

Energy production, demand, and cost data is sources from [Elexions](https://bmrs.elexon.co.uk/remit). Carbon tracking data is taken from [carbon_intensity.org](https://api.carbonintensity.org.uk/). 

Our Extract, Transform, Load [ETL] pipleine works in the following way; firstly, **E**xtract scripts for each API endpoint run regularly on Amazon Web Service [AWS] Lambdas requesting the latest data. Lambdas are quick to fire up and shut down, making them the ideal choice to quickly execute lightweight, intermittent tasks. This fresh data is then transferred to an AWS 's3 bucket', offering a quick and cost-effective storage. Some modest data curation is done by a **T**ransform script, and a **L**oad script loads the clean data into a PostGres SQL database on the AWS. For a full-scale and not a proof-of-concept project, we would ideally use an Amazon RedShift database which better supports read-heavy operations. In our limited instance, the inexpensive PostGres database is the best solution.

Another script runs our [StreamLit](https://streamlit.io) dashboard. StreamLit is an open-source dashboard solution that is easy to work with and lightweight to run. The dashboard, running perpetually as a service on an EC2 instance, reads data from our database and plots it in a pleasing set of graphs.

## Road Map

Where could we go next?

Elexon offers a lot more data that we could integrate, and energy suppliers like Octopus offer detailed insight which might allow users to add their personal energy usage to the dashboard.

## Support

If you are having trouble using our app please open a ticket we'll get back to you as soon as possible. 

## Authors and Acknowledgment

If people have pushed to this repo, they are authors!

## License

MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.





