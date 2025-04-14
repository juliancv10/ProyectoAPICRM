
from fastapi import FastAPI, Query, HTTPException 
from datetime import datetime
from db import get_connection
import uvicorn
import logging
from fastapi import Depends
from auth import verificar_token
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

load_dotenv()  # Carga variables del archivo .env

TOKEN = os.getenv("API_TOKEN")

app = FastAPI()
security = HTTPBearer()

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


# Configurar logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@app.get("/pacientes")
def get_pacientes(
    fecha_inicio: str = Query(..., description="Fecha de inicio en formato YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Fecha de fin en formato YYYY-MM-DD"),
    token: HTTPAuthorizationCredentials = Depends(verificar_token)
):
    logging.info(f"📥 Solicitud recibida - Fecha inicio: {fecha_inicio}, Fecha fin: {fecha_fin}, Token Valido")

    try:
        # Validar formato de fechas y convertir a objetos datetime
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")

        # Verificar que fecha_inicio sea menor o igual a fecha_fin
        if fecha_inicio_dt > fecha_fin_dt:
            raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser mayor que la fecha de fin.")

        # Calcular la diferencia en días
        diferencia_dias = (fecha_fin_dt - fecha_inicio_dt).days
        if diferencia_dias > 31:
            raise HTTPException(status_code=400, detail="El rango de fechas no puede ser mayor a 31 días.")

        # Conexión a la BD y consulta
        logging.info("✅ Fechas validadas correctamente.")

        conn = get_connection()
        cursor = conn.cursor()

        base_query = f"""
----------------------INFORMACIÓN DE CONSULTA EXTERNA AGENDAMIENTO SERVINTE --------------
select unique
SUBSTR(pachis, 1, 2) || '_' || 'paciente' || '_' ||SUBSTR(pacide,1, 8)||SUBSTR(pacnom,1,2)||SUBSTR(pacap1,1,3) AS Id_Paciente,
					
																															 
pacnac as fechanacimiento,
scs_f_bdbase_calculo_edad(citfci,pacnac,'01') edad,
pacsex as genero,
cittir as Tipo_Responsable,
citidr as Cod_Responsable,
citres as Nombre_Responsable, 
temdes as tipoempresa,
ctedetdes as segmento,
citfci fechaatencion,
espnom as especialidad,
ubinom as lugaregreso,
case when (citfci-pacnac)/365.25>=18 then 'ADULTO' Else 'PEDIATRICO' end Tipo_Paciente,
'CONSULTA EXTERNA' as tiposervicio,
pacdir as direccion,
paccoe as correo,
pactel as telefono,
paccel as celular,
'NO APLICA' as causaegreso,
painom as Paisresidencia,
munnom as municipioresidencia,
locnom as localidad,
estnom as estado_civil,
ocunom as ocupacion,
escdoccat as Tratamiento_de_datos_personales,
case 
	            WHEN epicitest ='SA' THEN 'SALIDA'
	            WHEN epicitest ='PF' THEN 'PENDIENTE FIRMA'
	            WHEN epicitest ='PR' THEN 'PRESENTADO'
	            WHEN epicitest ='SP' THEN 'SIN PRESENTARSE'
	            WHEN epicitest ='IN' THEN 'INASISTENTE'        
	            WHEN epicitest ='EP' THEN 'EN PROCESO'
	            WHEN epicitest ='RM' THEN 'REGISTRO MANUAL' 
                  when epicitest ='NA' then 'NO ATENDIDO'
	            END estado_tablero_consulta_ext,
	            case 
	            WHEN CITEST='P' THEN 'PENDIENTE'
	            WHEN CITEST='I' THEN 'INCUMPLIDA'
	            WHEN CITEST='C' THEN 'CANCELADO'  
	            WHEN CITEST='T' THEN 'ATENDIDO'
	            WHEN CITEST='A' THEN 'ATENDIDO'
	            WHEN CITEST='S' THEN 'SANCION'
	            END estado_citas_medicas
	       	     	from cncit INNER JOIN abpac ON abpac.pachis = cncit.cithis 
							INNER JOIN inesp ON citesp=espcod 
							inner JOIN cncon ON citcon=concod
							INNER JOIN cnconead ON citcon=coneadcod
							inner JOIN inubi ON coneadcub=ubicod
						  LEFT OUTER JOIN INMUN ON ABPAC.PACMUN = INMUN.MUNCOD
							left outer join hiepicit  on citdoc=epicitdoc AND EPICITFUE=CITFUE
						  LEFT OUTER JOIN ABPACOTR ON pacotrsec=PACHIS
						  left outer join inocu on ocucod=pacotrocu
						  left outer join inest on estcod=pacest
						  left outer join inloc on loccod=pacloc 
						  left outer join inpai on paicod=pacrpa
						  left outer join inemp on empcod=citidr
						  left outer join INTEM on temcod=emptip
							left outer join sictedet on empcod=ctedetpar and ctedetcod='CSSEG'
						left outer join HIESCDOC on escdocepi=epicitepi and UPPER(escdoccat) LIKE '%TRATAMIENTO DE DATOS%'
							where citfci between '{fecha_inicio}' and '{fecha_fin}'
		
UNION ALL			
-------------------------------------BASE DE DATOS DE PACIENTES EGRESADOS POR CAUSA DE SALIDA A CASA POR EL SERVICIO DE URGENCIAS----------------------------------------

select unique
SUBSTR(pachis, 1, 2) || '_' || 'paciente' || '_' ||SUBSTR(pacide,1, 8)||SUBSTR(pacnom,1,2)||SUBSTR(pacap1,1,3) AS Id_Paciente,
					
																															 
pacnac as fechanacimiento,
scs_f_bdbase_calculo_edad(egregr,pacnac,'01') edad,
pacsex as genero,
egremp as Tipo_Responsable,
egrcer as Cod_Responsable,
empnom as Nombre_Responsable, 
temdes as tipoempresa,
ctedetdes as segmento,
egregr as fechaatencion,
espnom as especialidad,
ubinom as lugaregreso,
 case when (egregr -pacnac)/365.25>=18 then 'ADULTO' Else 'PEDIATRICO' end Tipo_Paciente,
'URGENCIAS' as tiposervicio,
pacdir as direccion,
paccoe as correo,
pactel as telefono,
paccel as celular,
caunom as causaegreso,
painom as Paisresidencia,
munnom as municipioresidencia,
locnom as localidad,
estnom as estado_civil,
ocunom as ocupacion,
escdoccat as Tratamiento_de_datos_personales,
'NO APLICA' as estado_tablero_consulta_ext,
'NO APLICA' as estado_citas_medicas 
from inmegr 
						inner join inmed on medcod = egrmed  
             inner join inemp on empcod = egrcer
             inner join ABPAC on egrhis = pachis
             left outer join abpacotr on pacotrsec=abpac.pachis
             inner join inmdia on egrhis = mdiahis and egrnum = mdianum
             inner join inmesp on egrhis = mesphis  and egrnum = mespnum
             inner join inesp on mespesp = espcod
             inner join inser on egrseg = sercod
             inner join incau on egrcau = caucod
             inner join inmun on pacmun=muncod
             inner join indep on mundep = depcod
             left outer join inmpro on egrhis=mprohis and  egrnum = mpronum and (mprotip is null and mprotip='P')
             inner join hiepiina on epiinahis=egrhis and epiinanum=egrnum and epiinatep in ('URGE','HOSP')
             left outer join hhregcli on regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso') and hhregcli.regclisec=(select max(regclisec)from hhregcli where regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso'))
             left outer join inubi on ubicod=regcliubi
                 left outer join inocu on ocucod=pacotrocu
                left outer join inest on estcod=pacest
            left outer join inpai on paicod=pacnpa
             LEFT OUTER JOIN inmtra on trahis=egrhis  and tranum=egrnum  and inmtra.tradoc=(select max(tradoc)from inmtra where trahis=egrhis and tranum=egrnum)  
						  left outer join INTEM on temcod=emptip
							left outer join sictedet on empcod=ctedetpar and ctedetcod='CSSEG'
							left outer join inloc on loccod=pacloc 
							left outer join HIESCDOC on escdocepi=epiinaepi and UPPER(escdoccat) LIKE '%TRATAMIENTO DE DATOS%'
where egregr between '{fecha_inicio}' and '{fecha_fin}'
and egrhos='A'
AND mdiatip='P'
and egrseg in ('09','90')
and mesptip='P'
and egrcau='1'


UNION ALL

select  unique
SUBSTR(pachis, 1, 2) || '_' || 'paciente' || '_' ||SUBSTR(pacide,1, 8)||SUBSTR(pacnom,1,2)||SUBSTR(pacap1,1,3) AS Id_Paciente,
					
																															 
pacnac as fechanacimiento,
scs_f_bdbase_calculo_edad(egregr,pacnac,'01') edad,
pacsex as genero,
egremp as Tipo_Responsable,
'PAR' as Cod_Responsable,
'PARTICULAR' as Nombre_Responsable, 
'PARTICULAR' as tipoempresa,
'PARTICULAR' as segmento,
egregr as fechaatencion,
espnom as especialidad,
ubinom as lugaregreso,
 case when (egregr -pacnac)/365.25>=18 then 'ADULTO' Else 'PEDIATRICO' end Tipo_Paciente,
'URGENCIAS' as tiposervicio,
pacdir as direccion,
paccoe as correo,
pactel as telefono,
paccel as celular,
caunom as causaegreso,
painom as Paisresidencia,
munnom as municipioresidencia,
locnom as localidad,
estnom as estado_civil,
ocunom as ocupacion,
escdoccat as Tratamiento_de_datos_personales,
'NO APLICA' as estado_tablero_consulta_ext,
'NO APLICA' as estado_citas_medicas 
from inmegr
                  inner join abpac on egrhis=pachis
                  left outer join abpacotr on pacotrsec=abpac.pachis
                  inner join inmdia on egrhis=mdiahis and egrnum=mdianum
                  inner join inmesp on egrhis=mesphis and egrnum=mespnum
                  inner join inesp on  mespesp=espcod  
                  inner join inser on egrseg=sercod
                  inner join incau on egrcau=caucod
                  inner join inmun on pacmun=muncod
                  inner join indep on mundep= depcod
                  left outer join inmpro on egrhis=mprohis and  egrnum = mpronum and (mprotip is null and mprotip='P')
                  left outer join inpro on  mpropro=procod
                  inner join hiepiina on epiinahis=egrhis and epiinanum=egrnum and epiinatep in ('URGE','HOSP')
                  left outer join hhregcli on regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso') and hhregcli.regclisec=(select max(regclisec)from hhregcli where regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso'))
                  left outer join inubi on ubicod=regcliubi
                      left outer join inocu on ocucod=pacotrocu
                    left outer join inest on estcod=pacest
            left outer join inpai on paicod=pacnpa
                  LEFT OUTER JOIN inmtra on trahis=egrhis  and tranum=egrnum  and inmtra.tradoc=(select max(tradoc)from inmtra where trahis=egrhis and tranum=egrnum)
    							left outer join inloc on loccod=pacloc 
    							left outer join HIESCDOC on escdocepi=epiinaepi and UPPER(escdoccat) LIKE '%TRATAMIENTO DE DATOS%'
   where egremp = 'P'
    and egregr between '{fecha_inicio}' and '{fecha_fin}'
and egrhos='A'
AND mdiatip='P'
and egrseg in ('09','90')
and mesptip='P'
and egrcau='1'

-------------------------------------BASE DE DATOS DE PACIENTES EGRESADOS POR CAUSA DE SALIDA A CASA POR EL SERVICIO DE HOSPITALIZACIÓN----------------------------------------
UNION ALL

select unique
SUBSTR(pachis, 1, 2) || '_' || 'paciente' || '_' ||SUBSTR(pacide,1, 8)||SUBSTR(pacnom,1,2)||SUBSTR(pacap1,1,3) AS Id_Paciente,
					
																															 
pacnac as fechanacimiento,
scs_f_bdbase_calculo_edad(egregr,pacnac,'01') edad,
pacsex as genero,
egremp as Tipo_Responsable,
egrcer as Cod_Responsable,
empnom as Nombre_Responsable, 
temdes as tipoempresa,
ctedetdes as segmento,
egregr as fechaatencion,
espnom as especialidad,
ubinom as lugaregreso,
 case when (egregr -pacnac)/365.25>=18 then 'ADULTO' Else 'PEDIATRICO' end Tipo_Paciente,
'HOSPITALIZACIÓN' as tiposervicio,
pacdir as direccion,
paccoe as correo,
pactel as telefono,
paccel as celular,
caunom as causaegreso,
painom as Paisresidencia,
munnom as municipioresidencia,
locnom as localidad,
estnom as estado_civil,
ocunom as ocupacion,
escdoccat as Tratamiento_de_datos_personales,
'NO APLICA' as estado_tablero_consulta_ext,
'NO APLICA' as estado_citas_medicas 
from inmegr 
						inner join inmed on medcod = egrmed  
             inner join inemp on empcod = egrcer
             inner join ABPAC on egrhis = pachis
             left outer join abpacotr on pacotrsec=abpac.pachis
             inner join inmdia on egrhis = mdiahis and egrnum = mdianum
             inner join inmesp on egrhis = mesphis  and egrnum = mespnum
             inner join inesp on mespesp = espcod
             inner join inser on egrseg = sercod
             inner join incau on egrcau = caucod
             inner join inmun on pacmun=muncod
             inner join indep on mundep = depcod
             left outer join inmpro on egrhis=mprohis and  egrnum = mpronum and (mprotip is null and mprotip='P')
             inner join hiepiina on epiinahis=egrhis and epiinanum=egrnum and epiinatep in ('URGE','HOSP')
             left outer join hhregcli on regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso') and hhregcli.regclisec=(select max(regclisec)from hhregcli where regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso'))
             left outer join inubi on ubicod=regcliubi
                 left outer join inocu on ocucod=pacotrocu
                left outer join inest on estcod=pacest
            left outer join inpai on paicod=pacnpa
             LEFT OUTER JOIN inmtra on trahis=egrhis  and tranum=egrnum  and inmtra.tradoc=(select max(tradoc)from inmtra where trahis=egrhis and tranum=egrnum)  
						  left outer join INTEM on temcod=emptip
							left outer join sictedet on empcod=ctedetpar and ctedetcod='CSSEG'
							left outer join inloc on loccod=pacloc 
							left outer join HIESCDOC on escdocepi=epiinaepi and UPPER(escdoccat) LIKE '%TRATAMIENTO DE DATOS%'
where egregr between '{fecha_inicio}' and '{fecha_fin}'
and egrhos='H'
AND mdiatip='P'
and egrcau='1'


UNION ALL

select  unique
SUBSTR(pachis, 1, 2) || '_' || 'paciente' || '_' ||SUBSTR(pacide,1, 8)||SUBSTR(pacnom,1,2)||SUBSTR(pacap1,1,3) AS Id_Paciente,
					
																															 
pacnac as fechanacimiento,
scs_f_bdbase_calculo_edad(egregr,pacnac,'01') edad,
pacsex as genero,
egremp as Tipo_Responsable,
'PAR' as Cod_Responsable,
'PARTICULAR' as Nombre_Responsable, 
'PARTICULAR' as tipoempresa,
'PARTICULAR' as segmento,
egregr as fechaatencion,
espnom as especialidad,
ubinom as lugaregreso,
 case when (egregr -pacnac)/365.25>=18 then 'ADULTO' Else 'PEDIATRICO' end Tipo_Paciente,
'HOSPITALIZACIÓN' as tiposervicio,
pacdir as direccion,
paccoe as correo,
pactel as telefono,
paccel as celular,
caunom as causaegreso,
painom as Paisresidencia,
munnom as municipioresidencia,
locnom as localidad,
estnom as estado_civil,
ocunom as ocupacion,
escdoccat as Tratamiento_de_datos_personales,
'NO APLICA' as estado_tablero_consulta_ext,
'NO APLICA' as estado_citas_medicas 
from inmegr
                  inner join abpac on egrhis=pachis
                  left outer join abpacotr on pacotrsec=abpac.pachis
                  inner join inmdia on egrhis=mdiahis and egrnum=mdianum
                  inner join inmesp on egrhis=mesphis and egrnum=mespnum
                  inner join inesp on  mespesp=espcod  
                  inner join inser on egrseg=sercod
                  inner join incau on egrcau=caucod
                  inner join inmun on pacmun=muncod
                  inner join indep on mundep= depcod
                  left outer join inmpro on egrhis=mprohis and  egrnum = mpronum and (mprotip is null and mprotip='P')
                  left outer join inpro on  mpropro=procod
                  inner join hiepiina on epiinahis=egrhis and epiinanum=egrnum and epiinatep in ('URGE','HOSP')
                  left outer join hhregcli on regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso') and hhregcli.regclisec=(select max(regclisec)from hhregcli where regcliepi=epiinaepi and REGCLIPRO in  ('chpegrhmu','chpegrmue','chpegrrem','chpegreso'))
                  left outer join inubi on ubicod=regcliubi
                      left outer join inocu on ocucod=pacotrocu
                    left outer join inest on estcod=pacest
            left outer join inpai on paicod=pacnpa
                  LEFT OUTER JOIN inmtra on trahis=egrhis  and tranum=egrnum  and inmtra.tradoc=(select max(tradoc)from inmtra where trahis=egrhis and tranum=egrnum)
    							left outer join inloc on loccod=pacloc 
    							left outer join HIESCDOC on escdocepi=epiinaepi and UPPER(escdoccat) LIKE '%TRATAMIENTO DE DATOS%'
   where egremp = 'P'
    and egregr between '{fecha_inicio}' and '{fecha_fin}'
    and egrhos='H'
AND mdiatip='P'
and egrcau='1'
"""

        logging.info(f"🔍 Ejecutando consulta SQL: {base_query}")

        cursor.execute(base_query)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if not results:
            logging.warning("⚠️ No se encontraron resultados")

        return results

    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha incorrecto. Usa YYYY-MM-DD.")
    
    except HTTPException as http_exc:
        # Re-lanzar la excepción para que FastAPI la maneje correctamente
        raise http_exc
    
    except Exception as e:
        logging.error(f"❌ Error en la consulta: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    finally:
        try:
            conn.close()
            logging.info("🔌 Conexión cerrada")
        except Exception:
            pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)