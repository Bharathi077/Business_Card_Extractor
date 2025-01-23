document.addEventListener('DOMContentLoaded', () => {
    const fileUpload = document.getElementById('file-upload');
    const uploadBtn = document.getElementById('upload-btn');
    const imagePreview = document.getElementById('image-preview');
    const dataBody = document.getElementById('data-body');
    const downloadBtn = document.getElementById('download-btn');
    const clearBtn = document.getElementById('clear-btn');

    // Image preview
    fileUpload.addEventListener('change', (e) => {
        imagePreview.innerHTML = '';
        Array.from(e.target.files).forEach(file => {
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = document.createElement('img');
                img.src = event.target.result;
                imagePreview.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    });

    // Upload and extract images
    uploadBtn.addEventListener('click', async () => {
        const files = fileUpload.files;

        if (files.length === 0) {
            alert('Please select at least one image');
            return;
        }

        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.error) {
                alert(result.error);
                return;
            }

            // Populate table
            dataBody.innerHTML = '';
            result.data.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.person_name || 'N/A'}</td>
                    <td>${row.company_name || 'N/A'}</td>
                    <td>${row.email || 'N/A'}</td>
                    <td>${row.contact_number || 'N/A'}</td>
                `;
                dataBody.appendChild(tr);
            });

            downloadBtn.style.display = 'block';
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during upload');
        }
    });

    // Download CSV
    downloadBtn.addEventListener('click', async () => {
        const tableRows = Array.from(dataBody.querySelectorAll('tr'));
        const data = tableRows.map(row => ({
            'person_name': row.cells[0].textContent,
            'company_name': row.cells[1].textContent,
            'email': row.cells[2].textContent,
            'contact_number': row.cells[3].textContent
        }));

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ data })
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'business_cards.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error:', error);
        }
    });

    // Clear data
    clearBtn.addEventListener('click', async () => {
        try {
            await fetch('/clear', { method: 'POST' });
            imagePreview.innerHTML = '';
            dataBody.innerHTML = '';
            fileUpload.value = '';
            downloadBtn.style.display = 'none';
        } catch (error) {
            console.error('Error:', error);
        }
    });
});
