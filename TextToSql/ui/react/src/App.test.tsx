import axios from 'axios';
import { TEXT_TO_SQL_URL } from './config';
import { exec } from 'child_process';

const apiTimeOutInSeconds = 300;

// Helper function to get the host IP
const getHostIP = () => {
  return new Promise<string>((resolve, reject) => {
    exec('hostname -I | awk \'{print $1}\'', (error, stdout, stderr) => {
      if (error) {
        reject(`Error fetching IP address: ${error.message}`);
      } else if (stderr) {
        reject(`Stderr: ${stderr}`);
      } else {
        resolve(stdout.trim());
      }
    });
  });
};

test('testing api with dynamic host', async () => {
  // Get the dynamic host IP
  const host = await getHostIP();
  console.log(host)

  const endpointUrl = `http://${host}:9090/v1/texttosql`;
  console.log(endpointUrl);


  const formData = {
    user: 'postgres',
    database: 'chinook',
    host: host,  // Dynamic IP
    password: 'testpwd',
    port: '5442',
  };

  const question = "Find the number of albums";

  const payload = {
    input_text: question,
    conn_str: formData,
  };

  const response = await axios.post(endpointUrl, payload);

  expect(response.status).toBe(200);

  const result = response.data.result;
  expect(result.hasOwnProperty('sql')).toBe(true);
  expect(result.hasOwnProperty('output')).toBe(true);
  expect(result.hasOwnProperty('input')).toBe(true);
  expect(result.input).toBe(question);

}, apiTimeOutInSeconds * 1000);
