import { spawn } from 'child_process';
import path from 'path';

export async function queryDatabase(query: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(process.cwd(), '..', 'query_database.py');
    const workingDir = path.join(process.cwd(), '..');
    
    const pythonProcess = spawn('python3', [scriptPath, query], {
      cwd: workingDir,
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    let stdout = '';
    let stderr = '';
    
    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error('Python stderr:', stderr);
        reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        return;
      }
      
      try {
        const result = JSON.parse(stdout);
        if (result.error) {
          reject(new Error(result.error));
        } else {
          resolve(result);
        }
      } catch (error) {
        console.error('Failed to parse JSON:', stdout);
        reject(error);
      }
    });
    
    pythonProcess.on('error', (error) => {
      reject(error);
    });
  });
}

