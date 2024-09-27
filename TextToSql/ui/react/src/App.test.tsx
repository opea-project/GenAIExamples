import axios from 'axios';
import { TEXT_TO_SQL_URL } from './config';

const apiTimeOutInSeconds = 120;

test('testing api', async () => {

  const formData = {
    user: 'postgres',
    database: 'chinook',
    host: '10.223.24.242',
    password: 'testpwd',
    port: '5442',
  };

  const question = "Find the number of albums";

  const payload = {
    input_text: question,
    conn_str: formData,
  };
  
  const response = await axios.post(`${TEXT_TO_SQL_URL}/texttosql`, payload);

  expect(response.status).toBe(200);

  const result = response.data.result;
  expect(result.hasOwnProperty('sql')).toBe(true);
  expect(result.hasOwnProperty('output')).toBe(true);
  expect(result.hasOwnProperty('input')).toBe(true);
  expect(result.input).toBe(question);

}, apiTimeOutInSeconds * 1000);
