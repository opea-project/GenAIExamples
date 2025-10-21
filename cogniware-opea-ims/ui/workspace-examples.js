/**
 * Workspace Examples for Natural Language Processing
 * Provides detailed text examples for each feature
 */

const workspaceExamples = {
    'code_generation': {
        title: '💻 Code Generation Examples',
        description: 'Generate complete projects, APIs, and functions using natural language',
        examples: [
            {
                label: '🌐 REST API Creation',
                text: 'Create a complete REST API in Python with Flask for managing a customer database with CRUD operations, authentication, and error handling'
            },
            {
                label: '📊 Data Processing Function',
                text: 'Write a Python function that calculates compound interest with monthly contributions, considering tax implications and inflation'
            },
            {
                label: '🔐 Authentication System',
                text: 'Generate a secure user authentication system with JWT tokens, password hashing, email verification, and role-based access control'
            },
            {
                label: '📈 Financial Calculator',
                text: 'Create a function to calculate loan EMI with principal, interest rate, and tenure, including amortization schedule generation'
            },
            {
                label: '🎨 Web Scraper',
                text: 'Build a web scraper that extracts product prices from e-commerce websites and stores them in a database with error handling'
            }
        ]
    },
    'browser': {
        title: '🌐 Browser Automation Examples',
        description: 'Automate web interactions and data extraction',
        examples: [
            {
                label: '📸 Screenshot Capture',
                text: 'Take a screenshot of google.com homepage at 1920x1080 resolution'
            },
            {
                label: '📊 Data Extraction',
                text: 'Extract all product names and prices from amazon.com search results for "laptops"'
            },
            {
                label: '📝 Form Filling',
                text: 'Fill out a contact form on example.com with name "John Doe", email "john@example.com" and message "Test message"'
            },
            {
                label: '🔍 Information Gathering',
                text: 'Navigate to wikipedia.org, search for "Artificial Intelligence" and extract the first paragraph of the article'
            },
            {
                label: '⬇️ File Download',
                text: 'Download the latest version of a CSV file from a financial reporting website'
            }
        ]
    },
    'database': {
        title: '🗄️ Database Query Examples',
        description: 'Generate SQL queries from natural language questions',
        examples: [
            {
                label: '👥 Customer Analytics',
                text: 'Show me all customers who made purchases over $1000 in the last month, sorted by total spending'
            },
            {
                label: '📊 Sales Report',
                text: 'Generate a monthly sales report grouped by product category with total revenue and average order value'
            },
            {
                label: '🔍 Complex Join',
                text: 'Find all orders with their customer details and product information where the order status is "pending" and order date is within last week'
            },
            {
                label: '📈 Trending Analysis',
                text: 'Identify the top 10 best-selling products in the last quarter with their sales trends compared to previous quarter'
            },
            {
                label: '💰 Financial Summary',
                text: 'Calculate total revenue, profit margin, and average transaction value for each sales region in the current year'
            }
        ]
    },
    'documents': {
        title: '📄 Document Processing Examples',
        description: 'Extract information and answer questions from documents',
        examples: [
            {
                label: '📋 Contract Analysis',
                text: 'Analyze the uploaded contract PDF and extract key terms: parties involved, effective date, termination clauses, and payment terms'
            },
            {
                label: '📊 Financial Report Q&A',
                text: 'From the uploaded financial report, what was the total revenue in Q4 and how does it compare to Q3?'
            },
            {
                label: '📄 Resume Screening',
                text: 'Extract candidate name, education, work experience, skills, and years of experience from the uploaded resume'
            },
            {
                label: '📝 Meeting Notes Summary',
                text: 'Summarize the key action items, decisions made, and follow-up tasks from the uploaded meeting notes document'
            },
            {
                label: '🔍 Research Paper Analysis',
                text: 'Extract the research methodology, key findings, and conclusions from the uploaded research paper PDF'
            }
        ]
    }
};

function renderExamplesSection(module) {
    const examples = workspaceExamples[module];
    if (!examples) return '';
    
    let html = `
        <div class="examples-section">
            <h4>💡 Example Prompts - Click to Use</h4>
            <p style="color: #666; margin-bottom: 16px;">Click any example below to automatically fill it in and try it:</p>
    `;
    
    examples.examples.forEach(example => {
        html += `
            <div class="example-item" onclick="useExample('${module}', \`${example.text.replace(/`/g, '\\`')}\`)">
                <div class="example-item-label">${example.label}</div>
                <div class="example-item-text">${example.text}</div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function useExample(module, exampleText) {
    console.log('useExample called:', module, exampleText.substring(0, 50) + '...');
    
    const moduleConfig = {
        'code_generation': 'nlCodeInput',
        'browser': 'nlBrowserInput',
        'database': 'nlDatabaseInput',
        'documents': 'nlDocumentsInput'
    };
    
    const inputId = moduleConfig[module];
    console.log('Looking for input:', inputId);
    
    if (inputId) {
        const input = document.getElementById(inputId);
        console.log('Input element found?', !!input);
        
        if (input) {
            input.value = exampleText;
            input.focus();
            console.log('✅ Example text set successfully');
            
            // Smooth scroll to input
            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Visual feedback
            input.style.transform = 'scale(1.02)';
            input.style.transition = 'transform 0.3s';
            setTimeout(() => {
                input.style.transform = 'scale(1)';
            }, 300);
        } else {
            console.error('❌ Input element not found:', inputId);
        }
    } else {
        console.error('❌ No input ID configured for module:', module);
    }
}

