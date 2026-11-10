
import {
    useEffect,
    useState
} from "react";


import Layout from "../components/Layout";


import api from "../services/api";


import {
    FaEnvelope,
    FaCheckCircle,
    FaTimesCircle,
    FaHistory,
    FaSearch
} from "react-icons/fa";




function History(){



const [history,setHistory]=useState([]);



const [filteredHistory,setFilteredHistory]=useState([]);



const [search,setSearch]=useState("");



const [loading,setLoading]=useState(true);






useEffect(()=>{


loadHistory();


},[]);








useEffect(()=>{


const result =
history.filter((item)=>


item.buyer_email
.toLowerCase()
.includes(
search.toLowerCase()
)


||

item.subject
.toLowerCase()
.includes(
search.toLowerCase()
)


||

item.status
.toLowerCase()
.includes(
search.toLowerCase()
)



);



setFilteredHistory(result);



},[
search,
history
]);









const loadHistory=async()=>{


try{


setLoading(true);



const res =
await api.get(
"/api/email-history"
);



setHistory(
res.data
);



setFilteredHistory(
res.data
);



}

catch(error){


console.log(error);


}


finally{


setLoading(false);


}



};






return (

<Layout>

<div className="
space-y-6
">




{/* HEADER */}



<div className="
bg-gradient-to-r
from-purple-600
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


<FaHistory

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

Email History

</h1>


<p className="
mt-2
text-purple-100
">

Track all email campaigns, delivery status and buyer communication history.

</p>


</div>



</div>


</div>









{/* STATISTICS CARDS */}



<div className="
grid
grid-cols-1
md:grid-cols-3
gap-6
">







{/* TOTAL EMAILS */}


<div className="
bg-white
rounded-2xl
shadow-md
p-6
flex
items-center
gap-4
">


<div className="
bg-blue-100
p-4
rounded-full
">


<FaEnvelope

className="
text-blue-600
text-2xl
"

/>


</div>



<div>


<p className="
text-gray-500
text-sm
">

Total Emails

</p>



<h2 className="
text-3xl
font-bold
">


{
history.length
}


</h2>



</div>



</div>









{/* SUCCESS */}



<div className="
bg-white
rounded-2xl
shadow-md
p-6
flex
items-center
gap-4
">


<div className="
bg-green-100
p-4
rounded-full
">


<FaCheckCircle

className="
text-green-600
text-2xl
"

/>


</div>




<div>


<p className="
text-gray-500
text-sm
">

Delivered

</p>


<h2 className="
text-3xl
font-bold
text-green-600
">


{


history.filter(

item=>

item.status
.toLowerCase()
.includes(
"success"
)

||

item.status
.toLowerCase()
.includes(
"sent"
)

).length


}



</h2>


</div>



</div>









{/* FAILED */}



<div className="
bg-white
rounded-2xl
shadow-md
p-6
flex
items-center
gap-4
">


<div className="
bg-red-100
p-4
rounded-full
">


<FaTimesCircle

className="
text-red-600
text-2xl
"

/>


</div>



<div>


<p className="
text-gray-500
text-sm
">

Failed

</p>



<h2 className="
text-3xl
font-bold
text-red-600
">


{


history.filter(

item=>

item.status
.toLowerCase()
.includes(
"failed"
)


).length



}



</h2>



</div>


</div>





</div>









{/* SEARCH BAR */}



<div className="
bg-white
rounded-2xl
shadow-md
p-6
">



<div className="
relative
w-full
md:w-96
">



<FaSearch

className="
absolute
left-4
top-4
text-gray-400
"

/>





<input


placeholder="
Search email history...
"


value={search}


onChange={(e)=>

setSearch(
e.target.value
)

}


className="
w-full
pl-12
pr-4
py-3
border
rounded-xl
outline-none
focus:ring-2
focus:ring-purple-500
"


/>



</div>



</div>









{/* LOADING */}



{


loading &&


<div className="
bg-white
rounded-2xl
shadow-md
p-8
text-center
">


<div className="
animate-pulse
text-gray-500
text-lg
">


Loading email history...


</div>



</div>



}





{

!loading && (


<div className="
bg-white
rounded-2xl
shadow-md
overflow-hidden
">



<div className="
overflow-x-auto
">


<table className="
w-full
text-left
">



<thead className="
bg-gray-100
">


<tr>


<th className="
px-6
py-4
font-semibold
">

Email

</th>



<th className="
px-6
py-4
font-semibold
">

Subject

</th>



<th className="
px-6
py-4
font-semibold
">

Status

</th>



<th className="
px-6
py-4
font-semibold
">

Sent At

</th>



</tr>



</thead>







<tbody>


{


filteredHistory.length===0


?

(


<tr>


<td

colSpan="4"

className="
text-center
py-12
"


>


<div className="
flex
flex-col
items-center
gap-3
text-gray-500
">


<FaEnvelope

className="
text-4xl
"

/>



<p className="
text-lg
font-medium
">

No Email History Found

</p>



<p className="
text-sm
">

Emails sent through campaigns will appear here.

</p>



</div>



</td>


</tr>


)





:


filteredHistory.map((item)=>(


<tr


key={item.id}


className="
border-t
hover:bg-gray-50
transition
"



>



{/* EMAIL */}



<td className="
px-6
py-4
">


<div className="
flex
items-center
gap-3
">


<div className="
bg-blue-100
p-2
rounded-lg
">


<FaEnvelope

className="
text-blue-600
"

/>


</div>



<span className="
text-gray-700
font-medium
">

{item.buyer_email}

</span>



</div>



</td>









{/* SUBJECT */}



<td className="
px-6
py-4
">


<p className="
font-medium
text-gray-800
">


{item.subject}



</p>


</td>









{/* STATUS */}



<td className="
px-6
py-4
">


{


item.status
.toLowerCase()
.includes(
"success"
)

||

item.status
.toLowerCase()
.includes(
"sent"
)


?

(


<span className="
flex
items-center
gap-2
bg-green-100
text-green-700
px-3
py-1
rounded-full
text-sm
font-semibold
w-fit
">


<FaCheckCircle/>


{item.status}


</span>


)



:


(


<span className="
flex
items-center
gap-2
bg-red-100
text-red-700
px-3
py-1
rounded-full
text-sm
font-semibold
w-fit
">


<FaTimesCircle/>


{item.status}


</span>



)


}



</td>









{/* DATE */}



<td className="
px-6
py-4
text-gray-600
">


{


new Date(
item.sent_at
)
.toLocaleString()



}



</td>







</tr>



))


}



</tbody>



</table>


</div>


</div>


)


}








</div>


</Layout>


);


}



export default History;