# Phenotyping GUI - Documentation

# Introduction
The Phenotyping GUI is a software written in Python to help the drone pilots (and eventually the researchers) manage all aspects of the pipeline, including weekly overview of data collection, data transfer and processing and analysis.

The file St_Phenotyping.py is the top node of the file structure. This is the page that references all the other streamlit pages and makes the navigation panel which links to them.

The Phenotyping GUI best supports dark mode, as some text on the page “Review Drone Flights” (St_review_flights.py) is hardcoded white, and therefore becomes invisible when run in light mode. To activate dark mode

A comprehensive list of packages and version numbers can be found in the file Pheno.yml. However, the main packages are: pandas, streamlit, matplotlib.pyplot and seaborn.



# Procedure to start the Phenotyping GUI
## First-time setup:
<ol>
  <li>Install Anaconda if it is not already installed. Miniconda might also be sufficient.</li>
  <li>Clone the repository or download a zip file and unzip it.</li>
  <li>Create a Python environment from the file <code>Pheno.yml</code> by using the command:
    <pre><code>conda env create -f Pheno.yml -n Pheno</code></pre>
    <ul>
      <li><strong>Note:</strong> During installation, you might be prompted to give administrator rights. This is not very important, and you can safely skip/deny it.</li>
    </ul>
  </li>
</ol>







## Setup the prompt:
<ol>
  <li>Start “Anaconda Prompt”.</li>
  <li>Activate the environment by the command:
    <pre><code>conda activate Pheno</code></pre>
  </li>

  <ul>
    <li><strong>Note:</strong> You can check which environments exist by using the command:
      <pre><code>conda info --envs</code></pre>
    </li>
  </ul>

  <li>Set the current path to the folder of the downloaded repository. For example:
    <pre><code>cd C:\USER\UAV-Data-Processing</code></pre>
  </li>
</ol>











## Start the Phenotyping GUI:
<ol>
  <li>Do the “Setup the prompt” procedure twice, so that you get two “Anaconda Prompt” windows.</li>
  <li>In one “Anaconda Prompt” window, you write:
    <pre><code>streamlit run St_Phenotyping.py</code></pre>
    <ul>
      <li><strong>Note:</strong> The browser window that appears is the browser window you will use as the Phenotyping GUI. If you accidentally close it, the URL for it should still show in the Anaconda Prompt window, and it should be: <a href="http://localhost:8501">http://localhost:8501</a></li>
    </ul>
  </li>
  <li>In the other “Anaconda Prompt” window, you write:
    <pre><code>streamlit run St_flight_details.py</code></pre>
    <ul>
      <li><strong>Note:</strong> The browser window that appears will contain an error. This is fine, and you can close this window after it has opened. It is just so that it runs in the background and is used when the user clicks to see details of a flight.</li>
    </ul>
  </li>
</ol>










## Start the processing status script (optional):
<ol>
  <li>Do the “Setup the prompt” procedure.</li>
  <li>Write:
    <pre><code>streamlit run modules/processing_status.py</code></pre>
    <ul>
      <li><strong>Note:</strong> This might take some seconds to run (5-120s) as it is going through all the flights and checking the processing status of each.</li>
    </ul>
  </li>
</ol>





## Database Structure
The data is stored locally in csv files on the shared drive in the location:
-	P:\PhenoCrop\0_csv



