
import {
    useState
} from "react";


import Layout from "../components/Layout";


import {
    FaCog,
    FaBuilding,
    FaEnvelope,
    FaLock,
    FaFilePdf,
    FaSave,
    FaCheckCircle
} from "react-icons/fa";





function Settings(){



const [smtpEmail,setSmtpEmail]=useState("");



const [appPassword,setAppPassword]=useState("");



const [companyName,setCompanyName]=useState("");



const [emailTemplate,setEmailTemplate]=useState("");



const [catalogue,setCatalogue]=useState(null);






const handleSave=()=>{


alert(

`Settings Saved Successfully!


Company:
${companyName}


SMTP Email:
${smtpEmail}`


);


};






return (

<Layout>


<div className="
space-y-6
">





{/* HEADER */}



<div className="
bg-gradient-to-r
from-blue-600
to-indigo-700
rounded-2xl
p-8
text-white
shadow-lg
">


<div className="
flex
items-center
gap-4
">


<div className="
bg-white/20
p-4
rounded-xl
">


<FaCog

className="
text-3xl
"

/>


</div>



<div>


<h1 className="
text-3xl
font-bold
">

Settings

</h1>



<p className="
mt-2
text-blue-100
">

Configure company details, SMTP email and campaign preferences.

</p>



</div>



</div>



</div>









{/* SETTINGS GRID */}



<div className="
grid
grid-cols-1
lg:grid-cols-2
gap-6
">









{/* COMPANY SETTINGS */}



<div className="
bg-white
rounded-2xl
shadow-md
p-8
">



<div className="
flex
items-center
gap-3
mb-6
">


<div className="
bg-blue-100
p-3
rounded-xl
">


<FaBuilding

className="
text-blue-600
"

/>


</div>



<h2 className="
text-xl
font-bold
">

Company Profile

</h2>



</div>








<label className="
font-semibold
text-gray-700
">

Company Name

</label>



<input


type="text"


placeholder="ABC Exports Pvt Ltd"


value={companyName}


onChange={(e)=>

setCompanyName(
e.target.value
)

}



className="
w-full
mt-2
px-4
py-3
border
rounded-xl
outline-none
focus:ring-2
focus:ring-blue-500
"


/>



</div>











{/* SMTP SETTINGS */}



<div className="
bg-white
rounded-2xl
shadow-md
p-8
">



<div className="
flex
items-center
gap-3
mb-6
">


<div className="
bg-green-100
p-3
rounded-xl
">


<FaEnvelope

className="
text-green-600
"

/>


</div>



<h2 className="
text-xl
font-bold
">

SMTP Configuration

</h2>



</div>








<label className="
font-semibold
text-gray-700
">

SMTP Email

</label>



<input


type="email"


placeholder="company@gmail.com"


value={smtpEmail}


onChange={(e)=>

setSmtpEmail(
e.target.value
)

}


className="
w-full
mt-2
mb-5
px-4
py-3
border
rounded-xl
outline-none
focus:ring-2
focus:ring-green-500
"


/>









<label className="
font-semibold
text-gray-700
">

Gmail App Password

</label>



<div className="
relative
">


<FaLock

className="
absolute
left-4
top-4
text-gray-400
"

/>



<input


type="password"


placeholder="Enter App Password"


value={appPassword}


onChange={(e)=>

setAppPassword(
e.target.value
)

}



className="
w-full
mt-2
pl-12
px-4
py-3
border
rounded-xl
outline-none
focus:ring-2
focus:ring-green-500
"


/>



</div>






</div>





</div>









{/* EMAIL TEMPLATE */}



<div className="
bg-white
rounded-2xl
shadow-md
p-8
">



<div className="
flex
items-center
gap-3
mb-6
">


<div className="
bg-purple-100
p-3
rounded-xl
">


<FaEnvelope

className="
text-purple-600
"

/>


</div>



<h2 className="
text-xl
font-bold
">

Default Email Template

</h2>



</div>








<textarea


rows="8"


placeholder={

`Dear Buyer,

We are pleased to introduce our premium export products...`

}


value={emailTemplate}


onChange={(e)=>

setEmailTemplate(
e.target.value
)

}



className="
w-full
border
rounded-xl
px-4
py-3
outline-none
focus:ring-2
focus:ring-purple-500
resize-none
"


>




</textarea>




</div>









{/* CATALOGUE UPLOAD */}



<div className="
bg-white
rounded-2xl
shadow-md
p-8
">



<div className="
flex
items-center
gap-3
mb-5
">


<div className="
bg-red-100
p-3
rounded-xl
">


<FaFilePdf

className="
text-red-600
"

/>


</div>



<h2 className="
text-xl
font-bold
">

Product Catalogue

</h2>



</div>








<label className="
border-2
border-dashed
rounded-xl
p-8
flex
flex-col
items-center
justify-center
cursor-pointer
hover:bg-gray-50
transition
">


<FaFilePdf

className="
text-4xl
text-red-500
mb-3
"

/>


<p className="
font-medium
">

Upload Product Catalogue PDF

</p>



<input


type="file"


accept=".pdf"


onChange={(e)=>

setCatalogue(
e.target.files[0]
)

}


className="
hidden
"


/>



</label>





{

catalogue &&


<p className="
mt-3
text-green-600
font-medium
">


✓ {catalogue.name}


</p>


}




</div>








{/* SAVE SETTINGS BUTTON */}



<div className="
flex
justify-end
">


<button


onClick={handleSave}


className="
flex
items-center
gap-3
bg-blue-600
hover:bg-blue-700
text-white
px-8
py-3
rounded-xl
font-semibold
shadow-md
transition
"


>


<FaSave/>


Save Settings


</button>


</div>









{/* CURRENT CONFIGURATION */}



<div className="
bg-white
rounded-2xl
shadow-md
p-8
">



<div className="
flex
items-center
gap-3
mb-6
">


<div className="
bg-green-100
p-3
rounded-xl
">


<FaCheckCircle

className="
text-green-600
"

/>


</div>



<h2 className="
text-xl
font-bold
">

Current Configuration

</h2>



</div>









<div className="
grid
grid-cols-1
md:grid-cols-2
gap-6
">








{/* COMPANY */}



<div className="
bg-gray-50
rounded-xl
p-5
">


<p className="
text-gray-500
text-sm
">

Company Name

</p>



<h3 className="
font-semibold
text-lg
mt-1
">


{

companyName

||

"Not Configured"

}


</h3>



</div>









{/* SMTP */}



<div className="
bg-gray-50
rounded-xl
p-5
">


<p className="
text-gray-500
text-sm
">

SMTP Email

</p>



<h3 className="
font-semibold
text-lg
mt-1
">


{

smtpEmail

||

"Not Configured"

}


</h3>



</div>






</div>









{/* TEMPLATE PREVIEW */}



<div className="
mt-6
">


<p className="
text-gray-500
text-sm
mb-2
">

Email Template Preview

</p>



<div className="
bg-gray-100
rounded-xl
p-5
min-h-[120px]
whitespace-pre-wrap
text-gray-700
">


{

emailTemplate

||

"No email template configured."

}


</div>



</div>








{/* CATALOGUE STATUS */}



<div className="
mt-6
bg-blue-50
rounded-xl
p-5
flex
items-center
gap-3
">


<FaFilePdf

className="
text-blue-600
text-xl
"

/>


<div>


<p className="
font-semibold
">

Product Catalogue

</p>



<p className="
text-gray-600
text-sm
">


{

catalogue

?

catalogue.name

:

"No catalogue uploaded"

}


</p>



</div>



</div>







</div>








</div>


</Layout>


);


}



export default Settings;