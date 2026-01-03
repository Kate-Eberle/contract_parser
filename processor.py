from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from pathlib import Path
from typing import Union

def process_document(file_path: Union[str, Path], converter: DocumentConverter) -> dict:
    """Process a document using the provided converter and return metadata."""
    try:
        print(f"\n Processing document: {Path(file_path).name}")

        # Convert document
        result = converter.convert(file_path)

        # Export to markdown
        markdown = result.document.export_to_markdown()

        # Extract metadata
        doc_info = {
            'file': Path(file_path).name, 
            'format': Path(file_path).suffix, 
            'status': 'Success',
            'markdown_length': len(markdown), 
            'preview': markdown[:200].replace('\n', ' ')
        }

        # Save output to output folder
        output_file = f"output/output_{Path(file_path).stem}.md"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        

        doc_info['output_file'] = output_file 

        print(f" Document processed successfully. Output saved to {output_file}")

        return doc_info
    
    
    except Exception as e:
        print(f" Error: {e}")
        return {
            'file': Path(file_path).name, 
            'format': Path(file_path).suffix, 
            'status': 'Failed', 
            'error': str(e)
        }
    
def main():
    print("=" * 60)
    print("Multi=Format Document Processor")
    print("=" * 60)
        
   #Documents to process
    data_in_path = Path('data_in')
    documents = list(data_in_path.glob('*.*'))

    # Initialize the converter
    pdf_options = PdfPipelineOptions()
    pdf_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pdf_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

    # Process all documents
    results = []
    for doc_path in documents: 
        result = process_document(doc_path, converter)
        results.append(result)

    # Print summary
    print("\n" + "=" * 60)
    print("Processing Summary:")
    print("=" * 60  )

    for result in results: 
        status_icon = "✅" if result['status'] == 'Success' else "❌"
        print(f"{status_icon} {result['file']} ({result['format']})")
        if result['status'] == 'Success':
            print(f"  - Output: {result['output_file']}")
            print(f"  - Markdown Length: {result['markdown_length']} characters")
            print(f"  - Preview: {result['preview']}")
        else: 
            print(f"  - Error: {result['error']}")
        print()

    success_count = sum(1 for r in results if r['status'] == 'Success')
    failure_count = sum(1 for r in results if r['status'] == 'Failed')
    
    print(f"Converted {success_count}/{len(results)} documetns successfully.")
    print(f"Failed to convert {failure_count} documents.")

if __name__ == "__main__":
    main()