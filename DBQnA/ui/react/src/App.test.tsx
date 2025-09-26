import axios from 'axios';
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
  const endpointUrl = `http://${host}:9090/v1/text2query`;
  const connUrl = `postgresql://postgres:testpwd@${host}:5442/chinook`;
  const question = "Find the total number of invoices.";

  const payload = {
    query: question,
    conn_type: "sql",
    conn_url: connUrl,
    conn_user: "postgres",
    conn_password: "testpwd",
    conn_dialect: "postgresql",
  };

  const response = await axios.post(endpointUrl, payload);

  expect(response.status).toBe(200);

  const result = response.data.result;
  console.log(result);
  expect(result.hasOwnProperty('sql')).toBe(true);
  expect(result.hasOwnProperty('output')).toBe(true);
  expect(result.hasOwnProperty('input')).toBe(true);
  expect(result.input.query).toBe(question);

}, apiTimeOutInSeconds * 1000);
