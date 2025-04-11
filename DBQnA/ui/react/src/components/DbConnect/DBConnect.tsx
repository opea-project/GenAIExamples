import React, { useState } from 'react';
import axios from 'axios';
import { Button, Text, TextInput, Title, Textarea, Loader } from '@mantine/core';
import { TEXT_TO_SQL_URL } from '../../config';
// import { notifications } from '@mantine/notifications';
import styleClasses from './dbconnect.module.scss'; // Importing the SCSS file

const DBConnect: React.FC = () => {
  const [formData, setFormData] = useState({
    user: 'postgres',
    database: 'chinook',
    host: '10.223.24.113',
    password: 'testpwd',
    port: '5442',
  });

  const [dbStatus, setDbStatus] = useState<string | null>(null);
  const [sqlStatus, setSqlStatus] = useState<string | null>(null);
  const [dberror, setDbError] = useState<string | null>(null);
  const [sqlerror, setSqlError] = useState<string | null>(null);
  const [question, setQuestion] = useState<string>('');
  const [sqlQuery, setSqlQuery] = useState<string | null>(null);
  const [queryOutput, setQueryOutput] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState(false);

  // Handle form input changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  // Handle question input changes
  const handleQuestionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(e.target.value);
  };

  // Handle form submission and API request
  const handleDBConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let api_response: Record<string, any>;
      api_response = await axios.post(`${TEXT_TO_SQL_URL}/postgres/health`, formData);

      setSqlStatus(null);
      setSqlError(null);

      if (api_response.data.status === 'success') {
        setDbStatus(api_response.data.message);
        setDbError(null);
        setIsConnected(true);
        setQuestion('');
        setSqlQuery(null);
        setQueryOutput(null);
      } else {
        setDbStatus(null);
        setIsConnected(false);
        setDbError(api_response.data.message); //response would contain error message in case of failure
        setSqlStatus(null);
      }
    } catch (err) {
      setDbError('Failed to connect to the database.');
      setIsConnected(false);
      setDbStatus(null);
      setSqlStatus(null);
    }
  };
  
  // Handle generating SQL query
  const handleGenerateSQL = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const payload = {
        input_text: question,
        conn_str: formData,
      };

      let api_response: Record<string, any>;
      api_response = await axios.post(`${TEXT_TO_SQL_URL}/text2sql`, payload);

      setSqlQuery(api_response.data.result.sql); // Assuming the API returns an SQL query
      setQueryOutput(api_response.data.result.output);
      setSqlError(null)
      setSqlStatus('SQL query output generated successfully')
    } catch (err) {
      setSqlError('Failed to generate SQL query output.');
    } finally {
      setIsLoading(false); // Stop loading
    }
  };

  return (
    <div className={styleClasses.dbconnectWrapper}>
      <div className={styleClasses.dbConnectSection}>
        <Title order={1}>DB Connection</Title>
        <form className={styleClasses.form} onSubmit={handleDBConnect}>
          <div className={styleClasses.inputField}>
            <TextInput
              label="Host"
              placeholder="Enter Host"
              name="host"
              value={formData.host}
              onChange={handleChange}
              required
            />
          </div>

          <div className={styleClasses.inputField}>
            <TextInput
              label="User"
              placeholder="Enter User"
              name="user"
              value={formData.user}
              onChange={handleChange}
              required
            />
          </div>

          <div className={styleClasses.inputField}>
            <TextInput
              label="Database Name"
              placeholder="Enter Database Name"
              name="database"
              value={formData.database}
              onChange={handleChange}
              required
            />
          </div>

          <div className={styleClasses.inputField}>
            <TextInput
              label="Password"
              placeholder="Enter Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          <div className={styleClasses.inputField}>
            <TextInput
              label="Port"
              placeholder="Enter Port"
              name="port"
              value={formData.port}
              onChange={handleChange}
              required
            />
          </div>

          <Button type="submit" className={styleClasses.submitButton} fullWidth>
            Connect
          </Button>
        </form>

        {dbStatus && <Text className={styleClasses.status}>Status: {dbStatus}</Text>}
        {dberror && <Text className={styleClasses.error}>Error: {dberror}</Text>}
      </div>

      {/* DBQnA Section */}
      <div className={styleClasses.text2SQLSection}>
        <Title order={1}>DBQnA</Title>
        {isConnected && (
          <form className={styleClasses.form} onSubmit={handleGenerateSQL}>
            <div className={styleClasses.sqlQuerySection}>
              <div className={styleClasses.inputField}>
                <label>Enter Your Question:</label>
                <Textarea
                  placeholder="Type Your Question Here"
                  value={question}
                  onChange={handleQuestionChange}
                  required
                />
              </div>
            </div>

            <Button type="submit" className={styleClasses.submitButton} fullWidth disabled={isLoading}>
            {isLoading ? <div className="loader-container"><Loader size="sm" /></div> : 'Generate SQL Query Output'}
            </Button>
          </form>
        )}

        {/* Display SQL query response */}
        {isConnected && sqlQuery && queryOutput && !isLoading && (
          <div className={styleClasses.sqlQuerySection}>
            <form className={styleClasses.form}>
              <div className={styleClasses.inputField}>
                <label>Generated SQL Query:</label>
                <Textarea value={sqlQuery.replace('\n', '')} readOnly />
                <label>Generated SQL Query Output:</label>
                <Textarea value={queryOutput.replace('</s>', '')} readOnly />
              </div>
            </form>
          </div>
        )}

        {/* Display SQL generation status, error if any */}
        {sqlStatus && !isLoading && <Text className={styleClasses.status}>Status: {sqlStatus}</Text>}
        {sqlerror && !isLoading && <Text className={styleClasses.error}>Error: {sqlerror}</Text>}

      </div>
    </div>
  );
};

export default DBConnect;
