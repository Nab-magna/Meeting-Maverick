type ExportService="notion"|"slack"|"gmail";

export async function handleExport(
    service:ExportService,
    setToast:(toast:{message:string;type:"success"|"error"}|null)=>void
){
    try{
        const response=await fetch(`http://localhost:8000/${service}`,{
            method:"POST"
        });
        const data =await response.json();
        if(response.ok)
        {
            setToast({
                message:`Successfully exported to ${capitalize(service)}`,
                type:"success",
            });
        }
        else{
            setToast({
                message:`${data.detail||`Failed to export to ${capitalize(service)}`}`,
                type:"error",
            });
        }
    }
    catch(err){
        setToast({
            message:`❌ Network error during ${capitalize(service)} export.`,
            type:"error",   
        });
    }
}

function capitalize(s:string){
    return s.charAt(0).toUpperCase()+s.slice(1);
}